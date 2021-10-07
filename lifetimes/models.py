from django.db import models
from pyvalem.formula import Formula as PVFormula
from pyvalem.stateful_species import StatefulSpecies as PVStatefulSpecies

from utils.models import ModelMixin


class Formula(ModelMixin, models.Model):
    """A data model representing a chemical formula of a stateless species, without regards to different isotopologues.
    It is highly recommended to only use the available class methods to interact with the database (get_from_* and
    create_from_*), as these are coded to handle the name canonicalization etc.
    """

    # The following fields should be compatible with ExoMol database itself (and the formula_str needs to be compatible
    # with pyvalem.formula.Formula)
    formula_str = models.CharField(max_length=16)
    name = models.CharField(max_length=64)

    # The following fields are auto-filled using pyvalem package, when using the class methods below for construction
    html = models.CharField(max_length=64)
    charge = models.SmallIntegerField()
    natoms = models.PositiveSmallIntegerField()

    @classmethod
    def get_from_formula_str(cls, formula_str):
        """The formula_str needs to be canonicalised formula compatible with pyvalem.formula.Formula argument.
        It is expected that only a single Formula instance with a given formula_str exists, otherwise this might lead
        to inconsistent behaviour.
        """
        return cls.objects.get(formula_str=formula_str)

    @classmethod
    def create_from_data(cls, formula_str, name):
        """A method for creation of new Formula instances. It is highly recommended to use this method to prevent
        multiple Formula duplicates, inconsistent fields, etc.
        Example:
            formula_str = 'H2O',
            name = 'Water'
        The arguments should be compatible with ExoMol database itself.
        """
        pyvalem_formula = PVFormula(formula_str)

        # ensure the passed formula_str is canonicalised (canonicalisation offloaded to pyvalem)
        if repr(pyvalem_formula) != formula_str:
            raise ValueError(f'Non-canonicalised formula {formula_str} passed, instead of {repr(pyvalem_formula)}')

        try:
            cls.get_from_formula_str(formula_str)
            # Only a single instance with the given formula_str should exist!
            raise ValueError(f'{cls._meta.object_name}({formula_str}) already exists!')
        except cls.DoesNotExist:
            pass

        return cls.objects.create(formula_str=formula_str, name=name, html=pyvalem_formula.html,
                                  charge=pyvalem_formula.charge, natoms=pyvalem_formula.natoms)

    def __str__(self):
        return self.formula_str


class Isotopologue(ModelMixin, models.Model):
    """A data model representing a particular isotopologue belonging to the corresponding Formula instance.
    It is highly recommended to only use the available class methods to interact with the database (get_from_* and
    create_from_*), as these are coded to handle the name canonicalization etc.

    The infrastructure is prepared for multiple Isotopologues belonging to a single Formula, but it is intended only
    to have a single Isotopologue per Formula (the most naturally abundant one). OneToOne field is therefore used,
    but it might be later changed to ForeignKey.

    At the moment, only one isotopologue with a given iso_formula_str might exist in the database, and this should be
    the ExoMol-recommended dataset. However, multiple datasets per Isotopologue might be implemented in the future,
    in that case, the get_from_* and create_from_* methods need to be re-implemented.
    """
    formula = models.OneToOneField(Formula, on_delete=models.CASCADE)

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
        It is expected that only a single Formula instance with a given formula_str exists, otherwise this
        might lead to inconsistent behaviour.
        """
        return cls.objects.get(formula__formula_str=formula_str)

    @classmethod
    def create_from_data(cls, formula, iso_formula_str, inchi_key, dataset_name, version):
        # noinspection SpellCheckingInspection
        """A method for creation of new Isotopologue instances. It is highly recommended to use this method to prevent
        duplicates, inconsistent fields, etc.
        Example:
            formula = Formula.get_from_formula_str('H2O'),
            iso_formula_str = '(1H)2(16O)',
            inchi_key = 'XLYOFNOQVPJJNP-OUBTZVSYSA-N',
            dataset_name = 'POKAZATEL',
            version = 20180501
        The arguments should be compatible with ExoMol database itself.
        """
        pyvalem_formula = PVFormula(iso_formula_str)

        # ensure the passed formula_str is canonicalised (canonicalisation offloaded to pyvalem)
        if repr(pyvalem_formula) != iso_formula_str:
            raise ValueError(f'Non-canonicalised formula {iso_formula_str} passed, instead of {repr(pyvalem_formula)}')
        # Only a single instance per iso_formula_str should live in the database:
        try:
            cls.get_from_iso_formula_str(iso_formula_str)
            raise ValueError(f'{cls._meta.object_name}({iso_formula_str}) already exists!')
        except cls.DoesNotExist:
            pass
        try:
            cls.get_from_formula_str(formula.formula_str)
            raise ValueError(f'{cls._meta.object_name}({cls._meta.object_name}({formula.formula_str})) already exists!')
        except cls.DoesNotExist:
            pass

        return cls.objects.create(formula=formula, iso_formula_str=iso_formula_str,
                                  iso_slug=pyvalem_formula.slug, inchi_key=inchi_key, dataset_name=dataset_name,
                                  version=version, html=pyvalem_formula.html, mass=pyvalem_formula.mass)

    def __str__(self):
        return str(self.formula)


class State(ModelMixin, models.Model):
    """A data model representing a stateful species. The stateless species is represented by the Isotopologue instance
    and its state is created by pyvalem.state compatible string.
    Only a single State instance belonging to the same Isotopologue and describing the same physical state should exist
    at any given time in the database. To ensure this, it is recommended to use available class methods for creating
    new instances.
    """
    isotopologue = models.ForeignKey(Isotopologue, on_delete=models.CASCADE)

    state_str = models.CharField(max_length=64)
    lifetime = models.FloatField()
    energy = models.FloatField()

    state_html = models.CharField(max_length=64)

    @classmethod
    def get_from_data(cls, isotopologue, state_str):
        """Example:
            isotopologue = Isotopologue.get_from_iso_formula_str('(12C)(16O)'),
            state_str = 'v=42'
        The state_str gets canonicalised using pyvalem package (where the __repr__ method on objects is meant to
        return a canonicalized representation of the given object).
        Only one instance for the given pair of arguments should exist in the database at any given time, otherwise it
        might lead to some inconsistent behaviour.
        """
        return cls.objects.get(isotopologue=isotopologue, state_str=cls.canonicalise_state_str(state_str))

    @classmethod
    def create_from_data(cls, isotopologue, state_str, lifetime, energy):
        """Example:
            isotopologue = Isotopologue.get_from_iso_formula_str('(12C)(16O)'),
            state_str = 'v=42',
            lifetime = 0.42e-42,
            energy = 0.42
        The state_str gets canonicalized, so the saved state_str might differ from the passed state_str. However,
        the State.get_from_data will also reflect the canonicalization, so if both methods are used, it is irrelevant
        under which state_str the instance gets saved into the database.
        """
        canonicalised_state_str = cls.canonicalise_state_str(state_str)
        # Only a single instance per isotopologue and state_str should ever exist:
        try:
            cls.objects.get(isotopologue=isotopologue, state_str=canonicalised_state_str)
            raise ValueError(f'{cls._meta.object_name}({isotopologue}, {canonicalised_state_str}) already exists!')
        except cls.DoesNotExist:
            pass

        if lifetime < 0:
            raise ValueError(f'State lifetime needs to be positive! Passed lifetime={lifetime}!')

        species_html = PVStatefulSpecies(f'M {canonicalised_state_str}').html
        assert species_html.startswith('M '), 'This should never be raised, only defense.'
        state_html = species_html.lstrip('M').strip()

        return cls.objects.create(isotopologue=isotopologue, state_str=canonicalised_state_str,
                                  lifetime=lifetime, energy=energy, state_html=state_html)

    @staticmethod
    def canonicalise_state_str(state_str):
        """Helper method canonicalizing the state_str using the pyvalem package.
        Example:
            State.canonicalise_state_str('v=*;1SIGMA-')  = '1Σ-;v=*',
            State.canonicalise_state_str('1SIGMA-; v=*') = '1Σ-;v=*',
            State.canonicalise_state_str('1Σ-;v=*')      = '1Σ-;v=*',
        """
        test_species = 'M'
        canonicalised_state_str = repr(PVStatefulSpecies(f'{test_species} {state_str}')).lstrip('M').strip()
        return canonicalised_state_str

    def __str__(self):
        return f'{self.isotopologue} ({self.state_str})'


class Transition(ModelMixin, models.Model):
    """A data model representing a transition between two states as a structure for partial lifetimes and branching
    ratios. Only a single Transition instance of any two initial and final states should exist
    at any given time in the database. To ensure this, it is recommended to use available class methods for creating
    new instances. The .get_from_* methods are also implemented to explicitly show what data uniquely identify each
    Transition instance.
    """
    initial_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='transition_from_set')
    final_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='transition_to_set')

    partial_lifetime = models.FloatField()
    branching_ratio = models.FloatField()
    d_energy = models.FloatField()

    @classmethod
    def get_from_states(cls, initial_state, final_state):
        """Example:
            initial_state = State.get_from_data(Isotopologue.get_from_formula_str('CO'), 'v=2'),
            final_state = State.get_from_data(Isotopologue.get_from_formula_str('CO'), 'v=1')
        """
        return cls.objects.get(initial_state=initial_state, final_state=final_state)

    @classmethod
    def create_from_data(cls, initial_state, final_state, partial_lifetime, branching_ratio):
        """Example:
            initial_state = State.get_from_data(Isotopologue.get_from_formula_str('CO'), 'v=2'),
            final_state = State.get_from_data(Isotopologue.get_from_formula_str('CO'), 'v=1'),
            partial_lifetime = 0.42e-42,
            branching_ratio = 0.42
        """
        if initial_state.isotopologue is not final_state.isotopologue:
            raise ValueError(f'Transition creation failed! States {initial_state} and {final_state} '
                             f'do not share the same isotopologue!')
        # Only a single instance per the states pair should ever exist:
        try:
            cls.objects.get_from_states(initial_state, final_state)
            raise ValueError(f'{cls._meta.object_name}({initial_state}, {final_state}) already exists!')
        except cls.DoesNotExist:
            pass

        # values validation:
        if partial_lifetime < 0:
            raise ValueError(f'Partial lifetime needs to be positive! Passed partial_lifetime={partial_lifetime}!')
        if branching_ratio < 0 or branching_ratio > 1:
            raise ValueError(f'Branching ratio needs to be in [0, 1]! Passed branching_ratio={branching_ratio}!')

        return cls.objects.create(initial_state=initial_state, final_state=final_state,
                                  partial_lifetime=partial_lifetime, branching_ratio=branching_ratio,
                                  d_energy=final_state.energy - initial_state.energy)

    def __str__(self):
        return f'{str(self.initial_state.isotopologue)}({self.initial_state.state_str} → {self.final_state.state_str})'
