from django.db import models
from pyvalem.formula import Formula as PVFormula

from elida.apps.mixins import ModelMixin
from elida.apps.state.utils import canonicalise_and_parse_el_state_str, get_el_state_html
from .exceptions import MoleculeError


class Molecule(ModelMixin, models.Model):
    """A data model representing a molecule of a stateless species, without regards to different isotopologues.
    It is highly recommended to only use the available class methods to interact with the database (get_from_* and
    create_from_*), as these are coded to handle the name canonicalization etc.
    """

    # The following fields should be compatible with ExoMol database itself (and the formula_str needs to be compatible
    # with pyvalem.formula.Formula)
    formula_str = models.CharField(max_length=16)
    slug = models.CharField(max_length=16)
    name = models.CharField(max_length=64)

    # The following fields are auto-filled using pyvalem package, when using the class methods below for construction
    html = models.CharField(max_length=64)
    charge = models.SmallIntegerField()
    natoms = models.PositiveSmallIntegerField()

    @classmethod
    def get_from_formula_str(cls, formula_str):
        """The formula_str needs to be canonicalised formula compatible with pyvalem.formula.Formula argument.
        It is expected that only a single Molecule instance with a given formula_str exists, otherwise this might lead
        to inconsistent behaviour.
        """
        return cls.objects.get(formula_str=formula_str)

    @classmethod
    def create_from_data(cls, formula_str, name):
        """A method for creation of new Molecule instances. It is highly recommended to use this method to prevent
        multiple Molecule duplicates, inconsistent fields, etc.
        Example:
            formula_str = 'H2O',
            name = 'Water'
        The arguments should be compatible with ExoMol database itself.
        """
        pyvalem_formula = PVFormula(formula_str)

        # ensure the passed formula_str is canonicalised (canonicalisation offloaded to pyvalem)
        if repr(pyvalem_formula) != formula_str:
            raise MoleculeError(f'Non-canonicalised formula {formula_str} passed, instead of {repr(pyvalem_formula)}')

        try:
            cls.get_from_formula_str(formula_str)
            # Only a single instance with the given formula_str should exist!
            raise MoleculeError(f'{cls._meta.object_name}({formula_str}) already exists!')
        except cls.DoesNotExist:
            pass

        return cls.objects.create(formula_str=formula_str, slug=pyvalem_formula.slug, name=name,
                                  html=pyvalem_formula.html, charge=pyvalem_formula.charge,
                                  natoms=pyvalem_formula.natoms)

    def __str__(self):
        return self.formula_str

    @property
    def mass(self):
        return self.isotopologue.mass


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
    iso_slug = models.CharField(max_length=32)
    inchi_key = models.CharField(max_length=32)
    dataset_name = models.CharField(max_length=16)
    version = models.PositiveIntegerField()

    # The following fields will be autofilled by PyValem package when the class methods below are used for creation.
    html = models.CharField(max_length=64)
    mass = models.FloatField()

    # The following fields describe the meta-data about the dataset/states assigned to the molecule and isotopologue
    # (use dedicated methods defined to do this!):
    ground_el_state_str = models.CharField(max_length=64, default='')  # needs to be set if el. states are assigned
    vib_state_dim = models.SmallIntegerField(default=0)  # set automatically when vib states are assigned

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
            raise MoleculeError(f'{cls._meta.object_name}({iso_formula_str}) already exists!')
        except cls.DoesNotExist:
            pass
        try:
            cls.get_from_formula_str(molecule.formula_str)
            raise \
                MoleculeError(
                    f'{cls._meta.object_name}({cls._meta.object_name}({molecule.formula_str})) already exists!')
        except cls.DoesNotExist:
            pass

        return cls.objects.create(molecule=molecule, iso_formula_str=iso_formula_str,
                                  iso_slug=pyvalem_formula.slug, inchi_key=inchi_key, dataset_name=dataset_name,
                                  version=version, html=pyvalem_formula.html, mass=pyvalem_formula.mass)

    @property
    def transition_set(self):
        """Query set of all the transition objects involving states of this Isotopologue."""
        from elida.apps.transition.models import Transition
        return Transition.objects.filter(initial_state__isotopologue=self)

    def __str__(self):
        return str(self.molecule)

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
        n = self.molecule.natoms
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
