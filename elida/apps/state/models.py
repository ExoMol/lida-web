from django.db import models

from .utils import parse_and_validate_vib_state_str, canonicalise_el_state_str

from elida.apps.mixins import ModelMixin
from elida.apps.molecule.models import Isotopologue


class State(ModelMixin, models.Model):
    """A data model representing a stateful species. The stateless species is represented by the Isotopologue instance
    and its state is created by pyvalem.state compatible strings.
    Only a single State instance belonging to the same Isotopologue and describing the same physical state should exist
    at any given time in the database. To ensure this, it is recommended to use available class methods for creating
    new instances.
    """
    isotopologue = models.ForeignKey(Isotopologue, on_delete=models.CASCADE)

    lifetime = models.FloatField(null=True)  # null fields denoting float('inf') which are not supported in MySQL
    energy = models.FloatField()

    el_state_str = models.CharField(max_length=64)  # e.g. '1Σ-'
    vib_state_str = models.CharField(max_length=64)  # e.g. '(0, 1, 0, 3)'

    el_state_html = models.CharField(max_length=64)  # e.g. '<sup>1</sup>Σ<sup>-</sup>'
    vib_state_html = models.CharField(max_length=64)  # e.g. 'ν<sub>2</sub> + 3ν<sub>4</sub>'
    vib_state_html_alt = models.CharField(max_length=128)  # e.g. <b><i>v</i></b>=(0, 1, 0, 3)

    # TODO: change the input vibrational state string
    # TODO: check against vibrational dimensionality
    # TODO: check el_state against the ground state
    # TODO: all the html, canonicalisation, etc.

    # @classmethod
    # def get_from_data(cls, isotopologue, el_state_str='', vib_state_str=''):
    #     """Example:
    #         isotopologue = Isotopologue.get_from_iso_formula_str('(12C)(16O)'),
    #         vib_state_str = 'v=42',
    #         el_state_str = ''
    #     The state_str gets canonicalised using pyvalem package (where the __repr__ method on objects is meant to
    #     return a canonicalized representation of the given object).
    #     Only one instance for the given pair of arguments should exist in the database at any given time, otherwise it
    #     might lead to some inconsistent behaviour.
    #     """
    #     return cls.objects.get(isotopologue=isotopologue,
    #                            el_state_str=cls.canonicalise_state_str(el_state_str, 'el'),
    #                            vib_state_str=cls.canonicalise_state_str(vib_state_str, 'vib'))

    # @classmethod
    # def create_from_data(cls, isotopologue, lifetime, energy, el_state_str='', vib_state_str=''):
    #     """Example:
    #         isotopologue = Isotopologue.get_from_iso_formula_str('(12C)(16O)'),
    #         el_state_str = '1SIGMA-'
    #         vib_state_str = '(1, 0, 0)',
    #         lifetime = 0.42e-42,
    #         energy = 0.42
    #     The state_str gets canonicalized, so the saved state_str might differ from the passed state_str. However,
    #     the State.get_from_data will also reflect the canonicalization, so if both methods are used, it is irrelevant
    #     what state_str strings were used to save the state into the database.
    #     """
    #     if (not el_state_str) and (not vib_state_str):
    #         raise ValueError('At least one of electronic or vibrational states needs to be specified!')
    #
    #     canonicalised_el_state_str = cls.canonicalise_state_str(el_state_str, 'el')
    #     canonicalised_vib_state_str = cls.canonicalise_state_str(vib_state_str, 'vib')
    #     # Only a single instance per isotopologue and state_str should ever exist:
    #     try:
    #         cls.objects.get(isotopologue=isotopologue,
    #                         el_state_str=canonicalised_el_state_str,
    #                         vib_state_str=canonicalised_vib_state_str)
    #         raise ValueError(f'{cls._meta.object_name}({isotopologue}, {canonicalised_el_state_str}, '
    #                          f'{canonicalised_el_state_str}) already exists!')
    #     except cls.DoesNotExist:
    #         pass
    #
    #     if lifetime in {float('inf'), None}:
    #         lifetime = None
    #     elif lifetime < 0:
    #         raise ValueError(f'State lifetime needs to be positive! Passed lifetime={lifetime}!')
    #
    #     el_state_html = MolecularTermSymbol(canonicalised_el_state_str).html if canonicalised_el_state_str else ''
    #     vib_state_html = VibrationalState(canonicalised_vib_state_str).html if canonicalised_vib_state_str else ''
    #
    #     return cls.objects.create(isotopologue=isotopologue,
    #                               el_state_str=canonicalised_el_state_str,
    #                               vib_state_str=canonicalised_vib_state_str,
    #                               lifetime=lifetime, energy=energy,
    #                               el_state_html=el_state_html,
    #                               vib_state_html=vib_state_html)

    def __str__(self):
        molecule_str = str(self.isotopologue.molecule)
        state_str = ';'.join(s for s in [self.el_state_str, self.vib_state_str] if s)
        return f'{molecule_str} {state_str}'

    @property
    def species_html(self):
        molecule_html = self.isotopologue.molecule.html
        state_html = '; '.join(s for s in [self.el_state_html, self.vib_state_html] if s)
        return f'{molecule_html} {state_html}'
