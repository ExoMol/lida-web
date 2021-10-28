from django.test import TestCase

from elida.apps.molecule.models import Molecule, Isotopologue
from elida.apps.state.models import State
from elida.apps.transition.exceptions import TransitionError
from elida.apps.transition.models import Transition


# noinspection PyTypeChecker
class TestTransition(TestCase):
    def setUp(self):
        self.molecule = Molecule.create_from_data(formula_str='CO2', name='carbon dioxide')
        self.isotopologue = Isotopologue.create_from_data(self.molecule, iso_formula_str='(12C)(16O)2',
                                                          inchi_key='inchi_key', dataset_name='name', version=1)
        self.state_high = State.create_from_data(self.isotopologue, lifetime=0.1, energy=0.1, vib_state_str='(0, 0, 1)')
        self.state_low = State.create_from_data(self.isotopologue, lifetime=float('inf'), energy=-0.1,
                                                vib_state_str='(0, 0, 0)')

        self.diff_molecule = Molecule.create_from_data(formula_str='CO', name='carbon monoxide')
        self.diff_isotopologue = Isotopologue.create_from_data(self.diff_molecule, iso_formula_str='(12C)(16O)',
                                                               inchi_key='inchi_key', dataset_name='name', version=42)
        self.diff_state_high = State.create_from_data(self.diff_isotopologue, lifetime=0.01, energy=0.2,
                                                      vib_state_str='2')
        self.diff_state_low = State.create_from_data(self.diff_isotopologue, lifetime=0.1, energy=0.1,
                                                     vib_state_str='1')

    def test_str(self):
        tr = Transition.objects.create(initial_state=self.state_high, final_state=self.state_low,
                                       partial_lifetime=0.42, branching_ratio=0.42, delta_energy=0.42)
        self.assertEqual(str(tr), 'CO2 v=(0,0,1) → CO2 v=(0,0,0)')

    def test_repr(self):
        tr = Transition.objects.create(pk=42, initial_state=self.state_high, final_state=self.state_low,
                                       partial_lifetime=0.42, branching_ratio=0.42, delta_energy=0.42)
        self.assertEqual(repr(tr), '42:Transition(CO2 v=(0,0,1) → CO2 v=(0,0,0))')

    def test_get_from_states(self):
        with self.assertRaises(Transition.DoesNotExist):
            Transition.get_from_states(self.state_high, self.state_low)
        tr = Transition.objects.create(pk=42, initial_state=self.state_high, final_state=self.state_low,
                                       partial_lifetime=0.42, branching_ratio=0.42, delta_energy=0.42)
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
        self.assertEqual(tr.delta_energy, -0.2)

    def test_create_from_data_invalid(self):
        with self.assertRaises(TransitionError):
            Transition.create_from_data(self.state_high, self.state_low, partial_lifetime=0.1, branching_ratio=-0.1)
        with self.assertRaises(TransitionError):
            Transition.create_from_data(self.state_high, self.state_low, partial_lifetime=0.1, branching_ratio=1.1)
        with self.assertRaises(TransitionError):
            Transition.create_from_data(self.state_high, self.state_low, partial_lifetime=-0.1, branching_ratio=0.1)
        with self.assertRaises(TransitionError):
            Transition.create_from_data(self.diff_state_high, self.state_low, partial_lifetime=0.1, branching_ratio=0.1)
        with self.assertRaises(TransitionError):
            Transition.create_from_data(self.state_high, self.diff_state_low, partial_lifetime=0.1, branching_ratio=0.1)
        with self.assertRaises(TransitionError):
            Transition.create_from_data(self.state_high, self.state_high, partial_lifetime=0.1, branching_ratio=0.1)
        _ = Transition.create_from_data(self.state_high, self.state_low, partial_lifetime=0.1, branching_ratio=0.1)
        _ = Transition.create_from_data(self.diff_state_high, self.diff_state_low,
                                        partial_lifetime=0.1, branching_ratio=0.1)
        self.assertEqual(2, len(Transition.objects.all()))

    def test_delta_energy(self):
        t = Transition.create_from_data(self.state_high, self.state_low, partial_lifetime=0.1, branching_ratio=0.1)
        self.assertEqual(t.delta_energy, self.state_low.energy - self.state_high.energy)

    def test_html(self):
        t = Transition.create_from_data(self.state_high, self.state_low, partial_lifetime=0.1, branching_ratio=0.1)
        self.assertEqual(f'{self.state_high.html} → {self.state_low.html}', t.html)
