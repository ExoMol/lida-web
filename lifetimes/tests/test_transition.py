import numpy as np
from django.test import TestCase

from lifetimes.models import Formula, Isotopologue, State, Transition


# Create your tests here.
# noinspection PyTypeChecker
class TestTransition(TestCase):
    def setUp(self):
        self.formula = Formula.create_from_data(formula_str='CO2', name='carbon dioxide')
        self.isotopologue = Isotopologue.create_from_data(self.formula, iso_formula_str='(12C)(16O)2',
                                                          inchi_key='inchi_key', dataset_name='name', version=1)
        self.state_high = State.create_from_data(self.isotopologue, 'v=1', lifetime=0.1, energy=0.1)
        self.state_low = State.create_from_data(self.isotopologue, 'v=0', lifetime=float('inf'), energy=-0.1)
        self.state_none = State.create_from_data(self.isotopologue, '', lifetime=float('inf'), energy=0.)

        self.diff_formula = Formula.create_from_data(formula_str='CO', name='carbon monoxide')
        self.diff_isotopologue = Isotopologue.create_from_data(self.diff_formula, iso_formula_str='(12C)(16O)',
                                                               inchi_key='inchi_key', dataset_name='name', version=42)
        self.diff_state_high = State.create_from_data(self.diff_isotopologue, 'v=2', lifetime=0.01, energy=0.2)
        self.diff_state_low = State.create_from_data(self.diff_isotopologue, 'v=1', lifetime=0.1, energy=0.1)

    def test_str(self):
        tr = Transition.objects.create(initial_state=self.state_high, final_state=self.state_low,
                                       partial_lifetime=0.42, branching_ratio=0.42, d_energy=0.42)
        self.assertEqual(str(tr), 'CO2(v=1 → v=0)')
        tr = Transition.objects.create(initial_state=self.state_high, final_state=self.state_none,
                                       partial_lifetime=0.42, branching_ratio=0.42, d_energy=0.42)
        self.assertEqual(str(tr), 'CO2(v=1 → )')

    def test_repr(self):
        tr = Transition.objects.create(pk=42, initial_state=self.state_high, final_state=self.state_low,
                                       partial_lifetime=0.42, branching_ratio=0.42, d_energy=0.42)
        self.assertEqual(repr(tr), '42:Transition(CO2(v=1 → v=0))')

    def test_get_from_states(self):
        with self.assertRaises(Transition.DoesNotExist):
            Transition.get_from_states(self.state_high, self.state_low)
        tr = Transition.objects.create(pk=42, initial_state=self.state_high, final_state=self.state_low,
                                       partial_lifetime=0.42, branching_ratio=0.42, d_energy=0.42)
        with self.assertRaises(Transition.DoesNotExist):
            Transition.get_from_states(self.diff_state_high, self.state_low)
        with self.assertRaises(Transition.DoesNotExist):
            Transition.get_from_states(self.state_high, self.diff_state_low)
        self.assertEqual(tr, Transition.get_from_states(self.state_high, self.state_low))

    def test_create_from_data(self):
        self.assertEqual(0, len(Transition.objects.all()))
        tr = Transition.create_from_data(self.state_high, self.state_low, 0.1, 0.1)
        self.assertEqual(1, len(Transition.objects.all()))
        self.assertEqual(tr.branching_ratio, 0.1)
        self.assertEqual(tr.partial_lifetime, 0.1)
        self.assertEqual(tr.d_energy, -0.2)

    def test_create_from_data_invalid(self):
        with self.assertRaises(ValueError):
            Transition.create_from_data(self.state_high, self.state_low, partial_lifetime=0.1, branching_ratio=-0.1)
        with self.assertRaises(ValueError):
            Transition.create_from_data(self.state_high, self.state_low, partial_lifetime=0.1, branching_ratio=1.1)
        with self.assertRaises(ValueError):
            Transition.create_from_data(self.state_high, self.state_low, partial_lifetime=-0.1, branching_ratio=0.1)
        with self.assertRaises(ValueError):
            Transition.create_from_data(self.diff_state_high, self.state_low, partial_lifetime=0.1, branching_ratio=0.1)
        with self.assertRaises(ValueError):
            Transition.create_from_data(self.state_high, self.diff_state_low, partial_lifetime=0.1, branching_ratio=0.1)
        _ = Transition.create_from_data(self.state_high, self.state_low, partial_lifetime=0.1, branching_ratio=0.1)
        _ = Transition.create_from_data(self.diff_state_high, self.diff_state_low,
                                        partial_lifetime=0.1, branching_ratio=0.1)
        self.assertEqual(2, len(Transition.objects.all()))
