from django.db import models
from pyvalem.stateful_species import StatefulSpecies as PVStatefulSpecies

from elida.apps.mixins import ModelMixin
from elida.apps.molecule.models import Isotopologue


class State(ModelMixin, models.Model):
    """A data model representing a stateful species. The stateless species is represented by the Isotopologue instance
    and its state is created by pyvalem.state compatible string.
    Only a single State instance belonging to the same Isotopologue and describing the same physical state should exist
    at any given time in the database. To ensure this, it is recommended to use available class methods for creating
    new instances.
    """
    isotopologue = models.ForeignKey(Isotopologue, on_delete=models.CASCADE)

    state_str = models.CharField(max_length=64)
    lifetime = models.FloatField(null=True)  # null fields denoting float('inf') which are not supported in MySQL
    energy = models.FloatField()

    state_html = models.CharField(max_length=128)

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

        if lifetime in {float('inf'), None}:
            lifetime = None
        elif lifetime < 0:
            raise ValueError(f'State lifetime needs to be positive! Passed lifetime={lifetime}!')

        if canonicalised_state_str:
            species_html = PVStatefulSpecies(f'M {canonicalised_state_str}').html
            assert species_html.startswith('M '), 'This should never be raised, only defense.'
            state_html = species_html.lstrip('M').strip()
        else:
            state_html = ''

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
        if state_str.strip() == '':
            return ''
        test_species = 'M'
        canonicalised_state_str = repr(PVStatefulSpecies(f'{test_species} {state_str}')).lstrip('M').strip()
        return canonicalised_state_str

    def __str__(self):
        if self.state_str:
            return f'{self.isotopologue} ({self.state_str})'
        return f'{self.isotopologue}'
