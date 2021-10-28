from collections import OrderedDict

from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from pyvalem.vibrational_state import VibrationalState

from elida.apps.mixins import ModelMixin
from elida.apps.molecule.models import Isotopologue
from .exceptions import StateError
from .utils import validate_and_parse_vib_state_str, canonicalise_and_parse_el_state_str, get_state_str


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

    # el_state_str is compatible with pyvalem MolecularTermSymbol (what repr of the pyvalem class returns), e.g. '1Σ-'
    el_state_str = models.CharField(max_length=64)
    # vib_state_str is always a string and denoting either a vector or a single v,
    # e.g. '(0, 1, 0, 3)', '(0, 0, 0, 0)', and '5'
    vib_state_str = models.CharField(max_length=64)

    # the sync functions dict needs to be ordered, as the html attribute sync function expects el_state_html and
    # vib_state_html already synced
    sync_functions = OrderedDict([
        ('el_state_html', lambda state: canonicalise_and_parse_el_state_str(state.el_state_str)[1]),
        ('vib_state_html', lambda state: validate_and_parse_vib_state_str(state.vib_state_str)[1]),
        ('html', lambda state: state.get_html()),
        ('number_transitions_from', lambda state: state.transition_from_set.count()),
        ('number_transitions_to', lambda state: state.transition_to_set.count()),
    ])

    # following fields are auto-added when using the dedicated create_from methods (or the sync method).
    el_state_html = models.CharField(max_length=64)
    vib_state_html = models.CharField(max_length=64)
    html = models.CharField(max_length=128)
    # The following fields describe the meta-data about the transitions assigned to the state, handled automatically
    # when using the dedicated create_from methods...
    number_transitions_from = models.PositiveIntegerField()  # auto-inc/dec on transition creation/deletion
    number_transitions_to = models.PositiveIntegerField()  # auto-inc/dec on transition creation/deletion

    def __str__(self):
        return get_state_str(self.isotopologue, self.el_state_str, self.vib_state_str)

    @classmethod
    def get_from_data(cls, isotopologue, el_state_str='', vib_state_str=''):
        """Example:
            isotopologue = Isotopologue.get_from_iso_formula_str('(12C)(16O)'),
            el_state_str = '1SIGMA-',
            vib_state_str = '(42, 0, 0)',
        The el_state_str gets canonicalised using pyvalem package (where the __repr__ method on objects is meant to
        return a canonicalized representation of the given object).
        Only one instance for the given pair of arguments should exist in the database at any given time, otherwise it
        might lead to some inconsistent behaviour.
        """
        canonicalised_el_state_str, _ = canonicalise_and_parse_el_state_str(el_state_str)
        return cls.objects.get(
            isotopologue=isotopologue, el_state_str=canonicalised_el_state_str, vib_state_str=vib_state_str
        )

    @classmethod
    def create_from_data(cls, isotopologue, lifetime, energy, el_state_str='', vib_state_str=''):
        """Example:
            isotopologue = Isotopologue.get_from_iso_formula_str('(12C)(16O)'),
            el_state_str = '1SIGMA-'
            vib_state_str = '(1, 0, 0)',
            lifetime = 0.42e-42,
            energy = 0.42

        The state_str gets canonicalized, so the saved state_str might differ from the passed state_str. However,
        the State.get_from_data will also reflect the canonicalization, so if both methods are used, it is irrelevant
        what state_str strings were used to save the state into the database.

        The el_state_str needs to be compatible with pyvalem.molecular_term_symbol.MolecularTermSymbol class.

        The vib_state_str needs to be one of two options:
            'v', where v is a positive integer (e.g. '0', '2', ...)
            '(v1, v2, v3, ...v_n)', where v1-n are positive integers. E.g. '(0, 0, 0)', '(1, 2, 3, 5, 0)', ..., where
                                    the vector dimension is greater than 1.

        If the el_state_str is passed, the parent isotopologue needs to also have non-empty ground_el_state_str, which
        should match whatever el_state_str are present in the State instances representing electronic ground states.
        E.g., before creating states for SiH, which resolve 4 distinct electronic states {'A(2DELTA)', 'B(2SIGMA+)',
        'X(2PI)', 'a(4SIGMA+)'}, the string 'X(2PI)' needs to be fed into Isotopologue.set_ground_el_state_str, to
        identify, which of the resolved electronic states are the ground one. If the ground state is not set in the
        Isotopologue instance, feeding non-empty el_state_str will raise a StateError.

        If the vib_state_str is passed to the first State instance belonging to a certain Isotopologue, the
        Isotopologue.vib_state_dim gets populated with the dimension of the vibrational state vector.
        All other states created on the same Isotopologue instance need to match the same vibrational dimension,
        otherwise a StateError is raised.

        At least one of the two state strings need to be passed to any State instance and all the States belonging to
        one Isotopologue need to have consistent states (if all or none can have empty vib_state_str or all or none
        can have the empty el_state_str.)

        """
        if not el_state_str and not vib_state_str:
            raise StateError('At least one of electronic or vibrational states needs to be specified!')

        # ensure the passed el_state_str is valid and get canonicalised version and html.
        el_state_str, _ = canonicalise_and_parse_el_state_str(el_state_str)
        # the following also ensures that the passed vib_state_str is valid
        vib_state_quanta, _ = validate_and_parse_vib_state_str(vib_state_str)
        vib_state_dim = len(vib_state_quanta)

        # state_str is only for error reporting:
        state_str = get_state_str(isotopologue, el_state_str, vib_state_str)

        # Only a single instance per isotopologue and both state_str should ever exist:
        try:
            cls.objects.get(isotopologue=isotopologue, el_state_str=el_state_str, vib_state_str=vib_state_str)
            raise StateError(f'State "{state_str}" already exists!')
        except cls.DoesNotExist:
            pass

        # deal with the infinite lifetimes, swap for None
        if lifetime in {float('inf'), None}:
            lifetime = None
        elif lifetime < 0:
            raise StateError(f'Passed lifetime={lifetime} for State "{state_str}" is not positive!')

        # check if the vibrational state dimension matches the other states of the Isotopologue
        if vib_state_dim:
            if not isotopologue.state_set.count():
                # first State being saved for the given isotopologue
                isotopologue.set_vib_state_dim(vib_state_dim)
            elif isotopologue.vib_state_dim != vib_state_dim:
                raise StateError(
                    f'Vibrational dimension {vib_state_dim} of the state {state_str} does not match the vibrational '
                    f'dimension of the isotopologue {isotopologue}: {isotopologue.vib_state_dim}!'
                )
        elif isotopologue.vib_state_dim > 0:
            raise StateError(
                f'Isotopologue {isotopologue} expects vibrational dimension {isotopologue.vib_state_dim}, but State '
                f'{state_str} does not resolve vibrational states!'
            )
        # the same check with the electronic state, if resolved, the Isotopologue needs to know what a ground state is
        if el_state_str and not isotopologue.ground_el_state_str:
            raise StateError(
                f'Before saving State "{state_str}", ground_el_state_str needs to be saved for Isotopologue '
                f'{isotopologue}! Use Isotopologue.set_ground_el_state_str() once before saving any states resolving '
                f'electronic excitation.'
            )
        elif not el_state_str and isotopologue.ground_el_state_str:
            raise StateError(
                f'Isotopologue {isotopologue} has ground state defined and no electronic state is passed to the State'
                f'{state_str}! This is not allowed for consistency, all the states belonging to one Isotopologue must '
                f'define either vib_state_str, or el_state_str, or both. This is reflected by Isotopologue instance '
                f'by having vib_state_dim > 0 or non-empty ground_el_state_str.'
            )

        instance = cls(isotopologue=isotopologue, lifetime=lifetime, energy=energy, el_state_str=el_state_str,
                       vib_state_str=vib_state_str)
        instance.sync(propagate=False)
        isotopologue.sync(sync_only=['number_states'])
        return instance

    def get_html(self):
        molecule_html = self.isotopologue.molecule.html
        states_html = "; ".join(s for s in [self.el_state_html, self.vib_state_html] if s)
        return f'{molecule_html} {states_html}'

    @property
    def vib_state_str_alt(self):
        # vib_state_str_alt is a representation compatible with pyvalem VibrationalState (also canonicalised by repr)
        # e.g. 'v2+3v4' for vib_state_str == '(0, 1, 0, 3)', or 'v=5' for vib_state_str == '5'
        vib_state_quanta, _ = validate_and_parse_vib_state_str(self.vib_state_str)
        if not len(vib_state_quanta):
            raise StateError(f'Unrecognised vib_state_str saved under {self}!')
        elif len(vib_state_quanta) == 1:
            pyvalem_str = f'v={vib_state_quanta[0]}'
        elif not any(vib_state_quanta):
            return ''
        else:
            pyvalem_str = '+'.join(f'{q}v{v}' for v, q in enumerate(vib_state_quanta, start=1) if q > 0)

        vib_state_str_alt = repr(VibrationalState(pyvalem_str))
        return vib_state_str_alt

    @property
    def transition_set(self):
        from elida.apps.transition.models import Transition
        return Transition.objects.filter(models.Q(initial_state=self) | models.Q(final_state=self))


# noinspection PyUnusedLocal
@receiver(post_save)
@receiver(post_delete)
def sync_states(sender, instance, **kwargs):
    if sender == State:
        instance.isotopologue.sync(sync_only=['number_states'])
