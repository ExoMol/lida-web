from django.db import models
from pyvalem.formula import Formula as PVFormula

from .exceptions import MoleculeError
from .mixins import ModelMixin
from .molecule import Molecule
from .utils import canonicalise_and_parse_el_state_str, get_el_state_html


class Isotopologue(ModelMixin, models.Model):
    """A data model representing a particular isotopologue belonging to the corresponding Molecule instance.
    It is highly recommended to only use the available class methods to interact with the database (get_from_* and
    create_from_*), as these are coded to handle the name canonicalization etc.

    The infrastructure is prepared for multiple Isotopologues belonging to a single Molecule, but it is intended only
    to have a single Isotopologue per Molecule (the most naturally abundant one). OneToOne field is therefore used,
    but it might be later changed to ForeignKey.

    At the moment, only one isotopologue with a given iso_formula_str might exist in the database, and this should be
    the ExoMol-recommended dataset. However, multiple datasets per Isotopologue might be implemented in the future,
    in that case, the get_from_* and create_from_* methods need to be re-implemented.
    """
    molecule = models.OneToOneField(Molecule, on_delete=models.CASCADE)

    # The following fields refer directly to the ExoMol database itself.
    # One might use the fields for automatic checks for some new available data in the ExoMol database, or checks if the
    # recommended dataset_name has not changed.
    # iso_formula_str and iso_slug are compatible with PyValem package.
    iso_formula_str = models.CharField(max_length=32)
    inchi_key = models.CharField(max_length=32)
    dataset_name = models.CharField(max_length=16)
    version = models.PositiveIntegerField()

    # The following fields describe the meta-data about the dataset/states assigned to the molecule and isotopologue
    # (use dedicated methods defined to do this!):
    ground_el_state_str = models.CharField(max_length=64, default='')  # needs to be set if el. states are assigned
    vib_state_dim = models.PositiveSmallIntegerField(default=0)  # set automatically when vib states are assigned

    sync_functions = {
        'iso_slug': lambda iso: PVFormula(iso.iso_formula_str).slug,
        'html': lambda iso: PVFormula(iso.iso_formula_str).html,
        'mass': lambda iso: PVFormula(iso.iso_formula_str).mass,
        'number_states': lambda iso: iso.state_set.count(),
        'number_transitions': lambda iso: iso.transition_set.count(),
    }

    iso_slug = models.CharField(max_length=32)
    html = models.CharField(max_length=64)
    mass = models.FloatField()
    number_states = models.PositiveIntegerField()  # auto-increase/decrease on states creation/deletion
    number_transitions = models.PositiveIntegerField()  # auto-increase/decrease on states creation/deletion

    def __str__(self):
        return str(self.molecule)

    @classmethod
    def get_from_iso_formula_str(cls, iso_formula_str):
        """The iso_formula_str needs to be canonicalised formula compatible with pyvalem.formula.Formula argument.
        It is expected that only a single Isotopologue instance with a given iso_formula_str exists, otherwise this
        might lead to inconsistent behaviour.
        """
        return cls.objects.get(iso_formula_str=iso_formula_str)

    @classmethod
    def get_from_formula_str(cls, formula_str):
        """The formula_str needs to be canonicalised formula compatible with pyvalem.formula.Formula argument.
        It is expected that only a single Molecule instance with a given formula_str exists, otherwise this
        might lead to inconsistent behaviour.
        """
        if cls.objects.filter(molecule__formula_str=formula_str).count() > 1:
            raise MoleculeError('Looks like we have switched to one-to-many relationship between Molecule and '
                                'Isotopologue. In that case, this method needs to be revisited!')
        return cls.objects.get(molecule__formula_str=formula_str)

    @classmethod
    def create_from_data(cls, molecule, iso_formula_str, inchi_key, dataset_name, version):
        # noinspection SpellCheckingInspection
        """A method for creation of new Isotopologue instances. It is highly recommended to use this method to prevent
        duplicates, inconsistent fields, etc.
        Example:
            molecule = Molecule.get_from_formula_str('H2O'),
            iso_formula_str = '(1H)2(16O)',
            inchi_key = 'XLYOFNOQVPJJNP-OUBTZVSYSA-N',
            dataset_name = 'POKAZATEL',
            version = 20180501
        The arguments should be compatible with ExoMol database itself.
        """
        pyvalem_formula = PVFormula(iso_formula_str)

        # ensure the passed formula_str is canonicalised (canonicalisation offloaded to pyvalem)
        if repr(pyvalem_formula) != iso_formula_str:
            raise MoleculeError(
                f'Non-canonicalised formula {iso_formula_str} passed, instead of {repr(pyvalem_formula)}')
        # Only a single instance per iso_formula_str should live in the database:
        try:
            cls.get_from_iso_formula_str(iso_formula_str)
            raise MoleculeError(f'Isotopologue({iso_formula_str}) already exists!')
        except cls.DoesNotExist:
            pass
        try:
            cls.get_from_formula_str(molecule.formula_str)
            raise \
                MoleculeError(
                    f'Isotopologue(Molecule({molecule.formula_str})) already exists!')
        except cls.DoesNotExist:
            pass

        instance = cls(molecule=molecule, iso_formula_str=iso_formula_str, inchi_key=inchi_key,
                       dataset_name=dataset_name, version=version)
        instance.sync()
        instance.save()
        return instance

    @property
    def transition_set(self):
        """Query set of all the transition objects involving states of this Isotopologue."""
        from .transition import Transition
        return Transition.objects.filter(initial_state__isotopologue=self)

    def set_ground_el_state_str(self, ground_el_state_str):
        """Set the electronic ground state string representation belonging to this molecule. Should correspond to
        directly to the el_state_str field of some of the states of this Isotopologue. This will be used to determine
        which State instances are in fact ground states, even if containing explicit state strings.
        The state string gets canonicalised the same way as when saving new State instance.
        The ground state NEEDS to be saved manually, before any State instances containing el_state_str fields are
        attached to this Isotopologue, otherwise errors will be raised."""
        self.ground_el_state_str, _ = canonicalise_and_parse_el_state_str(ground_el_state_str)
        self.save()

    def set_vib_state_dim(self, vib_state_dim):
        """Method to define the dimensionality of the vibrational states resolved for this Molecule and Isotopologue.
        This value needs not be saved manually, rather it is saved the first time any State instance with resolved
        vibrational state is attached to the Isotopologue, and all the subsequently attached states need to be of the
        same dimensionality!"""
        if vib_state_dim < 0:
            raise MoleculeError('Vibrational state dimensionality cannot be negative!')
        n = self.molecule.number_atoms
        if n > 2:
            lim = 3 * n - 6
        elif n == 2:
            lim = 1
        else:
            lim = 0
        if vib_state_dim > lim:
            raise MoleculeError(f'Vibrational state dimensionality {vib_state_dim} higher than available number of '
                                f'degrees of freedom!')
        self.vib_state_dim = vib_state_dim
        self.save()

    @property
    def ground_el_state_html(self):
        return get_el_state_html(self.ground_el_state_str)

    @property
    def vib_quantum_numbers_html(self):
        if not self.vib_state_dim:
            return ''
        elif self.vib_state_dim == 1:
            return '<i>v</i>'
        else:
            return f"({', '.join([f'<i>v</i><sub>{i + 1}</sub>' for i in range(self.vib_state_dim)])})"

    @property
    def resolves_el(self):
        return bool(self.ground_el_state_str)

    @property
    def resolves_vib(self):
        return bool(self.vib_state_dim)