from django.test import TestCase
from pyvalem.state import StateParseError

from lifetimes.models import Formula, Isotopologue, State


# Create your tests here.
# noinspection PyTypeChecker
class TestState(TestCase):
    def setUp(self):
        self.formula = Formula.create_from_data(formula_str='CO2+', name='carbon dioxide ion')
        self.isotopologue = Isotopologue.create_from_data(self.formula, iso_formula_str='(12C)(16O)2+',
                                                          inchi_key='inchi_key', dataset_name='name', version=1)
        self.diff_formula = Formula.create_from_data(formula_str='CO', name='carbon monoxide')
        self.diff_isotopologue = Isotopologue.create_from_data(self.diff_formula, iso_formula_str='(12C)(16O)',
                                                               inchi_key='inchi_key', dataset_name='name',
                                                               version=1)

    def test_create_from_data(self):
        self.assertEqual(0, len(State.objects.all()))
        state_str_list = ['v=*', 'v=5', '1SIGMA-']
        for state_str in state_str_list:
            State.create_from_data(self.isotopologue, state_str, 0.42, 0.42)
        self.assertEqual(len(state_str_list), len(State.objects.all()))

    def test_create_from_data_invalid_state(self):
        self.assertEqual(0, len(State.objects.all()))
        with self.assertRaises(StateParseError):
            State.create_from_data(self.isotopologue, 'v;v', 0.42, 0.42)
        self.assertEqual(0, len(State.objects.all()))

    def test_create_from_data_invalid_values(self):
        self.assertEqual(0, len(State.objects.all()))
        with self.assertRaises(ValueError):
            State.create_from_data(self.isotopologue, state_str='v=0', lifetime=-0.1, energy=0.42)
        # negative energy allowed:
        _ = State.create_from_data(self.isotopologue, state_str='v=0', lifetime=0.1, energy=-0.42)
        self.assertEqual(1, len(State.objects.all()))

    def test_create_from_data_attributes(self):
        self.assertEqual(0, len(State.objects.all()))
        s = State.create_from_data(self.isotopologue, state_str='v=0', lifetime=0.42, energy=-0.42)
        self.assertEqual(self.isotopologue.pk, s.pk)
        self.assertEqual('v=0', s.state_str)
        self.assertEqual(0.42, s.lifetime)
        self.assertEqual(-0.42, s.energy)
        self.assertEqual('v=0', s.state_html)

    def test_create_from_data_duplicate(self):
        self.assertEqual(0, len(State.objects.all()))
        State.create_from_data(self.isotopologue, state_str='v=0', lifetime=0.42, energy=-0.42)
        with self.assertRaises(ValueError):
            State.create_from_data(self.isotopologue, state_str='v=0', lifetime=0, energy=0)
        State.create_from_data(self.isotopologue, state_str='v=1', lifetime=0.42, energy=-0.42)
        State.create_from_data(self.diff_isotopologue, state_str='v=0', lifetime=0.42, energy=-0.42)
        self.assertEqual(3, len(State.objects.all()))

    def test_create_from_data_canonicalization_duplicate(self):
        self.assertEqual(0, len(State.objects.all()))
        State.create_from_data(self.isotopologue, state_str='v=0;n=2;J=1/2', lifetime=0.42, energy=-0.42)
        for equivalent_state_str in ['v=0; n=2; J=1/2', 'v=0;J=1/2;n=2', 'n=2;J=1/2; v=0']:
            with self.assertRaises(ValueError):
                State.create_from_data(self.isotopologue, state_str=equivalent_state_str, lifetime=0, energy=0)
        self.assertEqual(1, len(State.objects.all()))

    def test_get_from_data(self):
        self.assertEqual(0, len(State.objects.all()))
        s = State.create_from_data(self.isotopologue, state_str='v=0;n=2;J=1/2', lifetime=0.42, energy=-0.42)
        self.assertEqual(1, len(State.objects.all()))
        self.assertEqual(s, State.get_from_data(self.isotopologue, state_str='v=0;n=2;J=1/2'))
        self.assertEqual(s, State.get_from_data(self.isotopologue, state_str='n=2;J=1/2;v=0'))
        with self.assertRaises(State.DoesNotExist):
            State.get_from_data(self.diff_isotopologue, state_str='v=0;n=2;J=1/2')
        with self.assertRaises(State.DoesNotExist):
            State.get_from_data(self.isotopologue, state_str='n=2;J=1/2')
        self.assertEqual(1, len(State.objects.all()))

    def test_canonicalise_state_str(self):
        state = 'v=0;n=2;1SIGMA-'
        for alternative_state in ['v=0;n=2;1Σ-', 'v=0;1SIGMA-;n=2', '1Σ-; v=0; n=2']:
            self.assertEqual(State.canonicalise_state_str(state), State.canonicalise_state_str(alternative_state))

    def test_str(self):
        self.assertEqual('CO (v=0)', str(State.create_from_data(self.diff_isotopologue, 'v=0', 0, 0)))
        self.assertEqual('CO (v=1)', str(State.create_from_data(self.diff_isotopologue, 'v=1', 0, 0)))
        self.assertEqual('CO', str(State.create_from_data(self.diff_isotopologue, '', 0, 0)))
        self.assertEqual('CO2+ (ν1+2ν2+3ν3)', str(State.create_from_data(self.isotopologue, '1v1+2v2+3v3', 0, 0)))
        self.assertEqual('CO2+', str(State.create_from_data(self.isotopologue, '', 0, 0)))

    def test_repr(self):
        s = State.create_from_data(self.isotopologue, 'v=0', 0, 0)
        self.assertEqual(f'{s.pk}:State(CO2+ (v=0))', repr(s))
        s = State.create_from_data(self.isotopologue, '', 0, 0)
        self.assertEqual(f'{s.pk}:State(CO2+)', repr(s))

    def test_infinite_lifetime(self):
        s = State.create_from_data(self.isotopologue, state_str='v=0', lifetime=float('inf'), energy=0)
        self.assertEqual(s.lifetime, None)
        s = State.create_from_data(self.isotopologue, state_str='v=2', lifetime=None, energy=0)
        self.assertEqual(s.lifetime, None)
        s = State.create_from_data(self.isotopologue, state_str='v=1', lifetime=42, energy=0)
        self.assertEqual(s.lifetime, 42)
