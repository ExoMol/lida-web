import re

from django.db import models
from pyvalem.formula import Formula as PVFormula

from .exceptions import MoleculeError
from .molecule import Molecule
from .utils import canonicalise_and_parse_el_state_str, get_el_state_html, BaseModel


class Isotopologue(BaseModel):
    """A data model representing a particular isotopologue belonging to the
    corresponding Molecule instance.
    It is highly recommended to only use the available class methods to interact with
    the database (get_from_* and create_from_*), as these are coded to handle the name
    canonicalization etc.

    The infrastructure is prepared for multiple Isotopologues belonging to a single
    Molecule, but it is intended only to have a single Isotopologue per Molecule
    (the most naturally abundant one). OneToOne field is therefore used,
    but it might be later changed to ForeignKey.

    At the moment, only one isotopologue with a given iso_formula_str might exist in
    the database, and this should be the ExoMol-recommended dataset. However,
    multiple datasets per Isotopologue might be implemented in the future,
    in that case, the get_from_* and create_from_* methods need to be re-implemented.

    Attributes
    ----------
    ground_el_state_str : str
        This field needs to be populated for the datasets which resolve electronic
        states. This needs to be populated self.set_ground_el_state_str method prior
        to instantiating any State objects belonging to this isotopologue instance.
        Normally, this will be the state_str belonging to the lowest-energy state
        in this dataset.
    vib_quantum_labels : str
        Example: "(v)", "(n1, n2, n3)", "(v1, v2lin, v3)", etc.
    vib_quantum_labels_html : str
        Example: "v", "(n<sub>1</sub>, n<sub>1</sub>, n<sub>1</sub>)", etc.
    vib_state_dim : int
        Example: 0 if vibrational states are not resolved, 1 for diatomic, etc.
    """

    molecule = models.OneToOneField(Molecule, on_delete=models.CASCADE)

    # The following fields refer directly to the ExoMol database itself.
    # One might use the fields for automatic checks for some new available data in the
    # ExoMol database, or checks if the recommended dataset_name has not changed.
    # iso_formula_str and iso_slug are compatible with PyValem package.
    iso_formula_str = models.CharField(max_length=32)
    dataset_name = models.CharField(max_length=16)
    version = models.PositiveIntegerField()

    # The following fields describe the meta-data about the dataset/states assigned to
    # the molecule and isotopologue (use dedicated methods defined to do this!):
    # ground state string needs to be set if el. states are assigned
    ground_el_state_str = models.CharField(max_length=64, default="", blank=True)
    # labels for the vibrational quanta (in a tuple form if polyatomic),
    # e.g. "v", "(v1, v2, v3)", "(n1, n2, n3, n4, n5, n6)", "(v1, v2lin, v3)"
    vib_quantum_labels = models.CharField(max_length=64, default="")
    # the html representation of the labels gets created automatically
    vib_quantum_labels_html = models.CharField(max_length=128, default="")
    # vibrational dimensionality set automatically when vib_quantum_labels are assigned
    vib_state_dim = models.PositiveSmallIntegerField(default=0)

    sync_functions = {
        "iso_slug": lambda iso: PVFormula(iso.iso_formula_str).slug,
        "html": lambda iso: PVFormula(iso.iso_formula_str).html,
        "mass": lambda iso: PVFormula(iso.iso_formula_str).mass,
        "number_states": lambda iso: iso.state_set.count(),
        "number_transitions": lambda iso: iso.transition_set.count(),
    }

    iso_slug = models.CharField(max_length=32)
    html = models.CharField(max_length=64)
    mass = models.FloatField()
    # auto-increase/decrease on states creation/deletion:
    number_states = models.PositiveIntegerField()
    number_transitions = models.PositiveIntegerField()

    def __str__(self):
        return str(self.molecule)

    @classmethod
    def get_from_iso_formula_str(cls, iso_formula_str):
        """The iso_formula_str needs to be canonicalised formula compatible with
        pyvalem.formula.Formula argument.
        It is expected that only a single Isotopologue instance with a given
        iso_formula_str exists, otherwise this might lead to inconsistent behaviour.
        """
        return cls.objects.get(iso_formula_str=iso_formula_str)

    @classmethod
    def get_from_formula_str(cls, formula_str):
        """The formula_str needs to be canonicalised formula compatible with
        pyvalem.formula.Formula argument.
        It is expected that only a single Molecule instance with a given formula_str
        exists, otherwise this might lead to inconsistent behaviour.
        """
        if cls.objects.filter(molecule__formula_str=formula_str).count() > 1:
            raise MoleculeError(
                "Looks like we have switched to one-to-many relationship between "
                "Molecule and Isotopologue. In that case, this method needs to be "
                "revisited!"
            )
        return cls.objects.get(molecule__formula_str=formula_str)

    @classmethod
    def create_from_data(cls, molecule, iso_formula_str, dataset_name, version):
        # noinspection SpellCheckingInspection
        """A method for creation of new Isotopologue instances. It is highly
        recommended to use this method to prevent duplicates, inconsistent fields, etc.
        Example:
            molecule = Molecule.get_from_formula_str('H2O'),
            iso_formula_str = '(1H)2(16O)',
            dataset_name = 'POKAZATEL',
            version = 20180501
        The arguments should be compatible with ExoMol database itself.
        """
        pyvalem_formula = PVFormula(iso_formula_str)

        # ensure the passed formula_str is canonicalised (canonicalisation offloaded to
        # pyvalem)
        if repr(pyvalem_formula) != iso_formula_str:
            raise MoleculeError(
                f"Non-canonicalised formula {iso_formula_str} passed, instead of "
                f"{repr(pyvalem_formula)}"
            )
        # Only a single instance per iso_formula_str should live in the database:
        try:
            cls.get_from_iso_formula_str(iso_formula_str)
            raise MoleculeError(f"Isotopologue({iso_formula_str}) already exists!")
        except cls.DoesNotExist:
            pass
        try:
            cls.get_from_formula_str(molecule.formula_str)
            raise MoleculeError(
                f"Isotopologue(Molecule({molecule.formula_str})) already exists!"
            )
        except cls.DoesNotExist:
            pass

        instance = cls(
            molecule=molecule,
            iso_formula_str=iso_formula_str,
            dataset_name=dataset_name,
            version=version,
        )
        instance.sync()
        return instance

    @property
    def transition_set(self):
        """Query set of all the transition objects involving states of this
        Isotopologue.
        """
        from .transition import Transition

        return Transition.objects.filter(initial_state__isotopologue=self)

    def set_ground_el_state_str(self, ground_el_state_str):
        """Set the electronic ground state string representation belonging to this
        molecule.
        Should correspond directly to the el_state_str field of some of the states of
        this Isotopologue. This will be used to determine which State instances are in
        fact ground states, even if containing explicit state strings.
        The state string gets canonicalised the same way as when saving new State
        instance.
        The ground state NEEDS to be saved manually, before any State instances
        containing el_state_str fields are attached to this Isotopologue, otherwise
        errors will be raised."""
        self.ground_el_state_str, _ = canonicalise_and_parse_el_state_str(
            ground_el_state_str
        )
        self.save()

    def _validate_vib_state_dim(self, vib_state_dim):
        """Method to define the dimensionality of the vibrational states resolved for
        this Molecule and Isotopologue.
        This value needs not be saved manually, rather it is saved the first time any
        State instance with resolved vibrational state is attached to the Isotopologue,
        and all the subsequently attached states need to be of the same dimensionality!
        """
        if vib_state_dim < 0:
            raise MoleculeError("Vibrational state dimensionality cannot be negative!")
        n = self.molecule.number_atoms
        if n > 2:
            lim = 3 * n - 6
        elif n == 2:
            lim = 1
        else:
            lim = 1 # 0 ALEC
        if vib_state_dim > lim:
            raise MoleculeError(
                f"Vibrational state dimensionality {vib_state_dim} higher than "
                f"available number of degrees of freedom!"
            )
        return vib_state_dim

    @staticmethod
    def _get_vib_quantum_labels_html(vib_quanta_labels):
        """
        Parameters
        ----------
        vib_quanta_labels : list[str]
        """
        pattern = re.compile(r"^([vn])(\d+)?(lin)?$")
        html_labels = []
        for label in vib_quanta_labels:
            match = pattern.match(label)
            if match is None:
                html_labels.append(label)
            else:
                letter, index, lin = match.group(1), match.group(2), match.group(3)
                label_html = letter
                if index is not None:
                    label_html = f"{label_html}<sub>{index}</sub>"
                if lin:
                    label_html = f"{label_html}<sup>{lin}</sup>"
                html_labels.append(label_html)
        if len(html_labels) == 1:
            vib_quantum_labels_html = html_labels[0]
        else:
            vib_quantum_labels_html = f'({", ".join(html_labels)})'
        return vib_quantum_labels_html

    @staticmethod
    def _split_vib_quantum_labels(vib_labels_str):
        return [l.strip() for l in vib_labels_str.lstrip("(").rstrip(")").split(",")]

    def set_vib_quantum_labels(self, vib_quantum_labels):
        """Set metadata about what the vibrational quanta values refer to.

        Also sets the vibrational state dimensionality as a side effect.

        Parameters
        ----------
        vib_quantum_labels : str
            either a simple "v", "n", if diatomic, or in the tuple form of
            "(v1, v2, v3)", "(n1, n2, n3, n4)", "(v1, v2lin, v3)", if polyatomic
        """
        labels = self._split_vib_quantum_labels(vib_quantum_labels)
        self.vib_quantum_labels = vib_quantum_labels
        self.vib_state_dim = self._validate_vib_state_dim(len(labels))
        self.vib_quantum_labels_html = self._get_vib_quantum_labels_html(labels)
        self.save()

    @property
    def ground_el_state_html(self):
        return get_el_state_html(self.ground_el_state_str)

    @property
    def resolves_el(self):
        return bool(self.ground_el_state_str)

    @property
    def resolves_vib(self):
        return bool(self.vib_state_dim)
