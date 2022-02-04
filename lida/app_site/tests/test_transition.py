from django.test import TestCase

from ..models import Molecule, Isotopologue, State, Transition
from ..models.exceptions import TransitionError


# noinspection PyTypeChecker
class TestTransition(TestCase):
    def setUp(self):
        self.molecule = Molecule.create_from_data(
            formula_str="CO2", name="carbon dioxide"
        )
        self.isotopologue = Isotopologue.create_from_data(
            self.molecule, iso_formula_str="(12C)(16O)2", dataset_name="name", version=1
        )
        self.state_high = State.create_from_data(
            self.isotopologue,
            lifetime=0.1,
            energy=0.1,
            vib_state_str="(0, 0, 1)",
            vib_state_labels="(v1, v2, v3)",
        )
        self.state_low = State.create_from_data(
            self.isotopologue,
            lifetime=float("inf"),
            energy=-0.1,
            vib_state_str="(0, 0, 0)",
            vib_state_labels="(v1, v2, v3)",
        )

        self.diff_molecule = Molecule.create_from_data(
            formula_str="CO", name="carbon monoxide"
        )
        self.diff_isotopologue = Isotopologue.create_from_data(
            self.diff_molecule,
            iso_formula_str="(12C)(16O)",
            dataset_name="name",
            version=42,
        )
        self.diff_state_high = State.create_from_data(
            self.diff_isotopologue,
            lifetime=0.01,
            energy=0.2,
            vib_state_str="2",
            vib_state_labels="n",
        )
        self.diff_state_low = State.create_from_data(
            self.diff_isotopologue,
            lifetime=0.1,
            energy=0.1,
            vib_state_str="1",
            vib_state_labels="n",
        )

    def test_str(self):
        tr = Transition.objects.create(
            initial_state=self.state_high,
            final_state=self.state_low,
            partial_lifetime=0.42,
            delta_energy=0.42,
        )
        self.assertEqual(str(tr), "CO2 v=(0,0,1) → CO2 v=(0,0,0)")

    def test_repr(self):
        tr = Transition.objects.create(
            pk=42,
            initial_state=self.state_high,
            final_state=self.state_low,
            partial_lifetime=0.42,
            delta_energy=0.42,
        )
        self.assertEqual(repr(tr), "42:Transition(CO2 v=(0,0,1) → CO2 v=(0,0,0))")

    def test_get_from_states(self):
        with self.assertRaises(Transition.DoesNotExist):
            Transition.get_from_states(self.state_high, self.state_low)
        tr = Transition.objects.create(
            pk=42,
            initial_state=self.state_high,
            final_state=self.state_low,
            partial_lifetime=0.42,
            delta_energy=0.42,
        )
        with self.assertRaises(Transition.DoesNotExist):
            Transition.get_from_states(self.diff_state_high, self.state_low)
        with self.assertRaises(Transition.DoesNotExist):
            Transition.get_from_states(self.state_high, self.diff_state_low)
        self.assertEqual(
            tr, Transition.get_from_states(self.state_high, self.state_low)
        )

    def test_create_from_data(self):
        self.assertEqual(0, len(Transition.objects.all()))
        tr = Transition.create_from_data(self.state_high, self.state_low, 0.1)
        self.assertEqual(1, len(Transition.objects.all()))
        self.assertEqual(tr.partial_lifetime, 0.1)
        self.assertEqual(tr.delta_energy, -0.2)

    def test_create_from_data_invalid(self):
        with self.assertRaises(TransitionError):
            Transition.create_from_data(
                self.state_high,
                self.state_low,
                partial_lifetime=-0.1,
            )
        with self.assertRaises(TransitionError):
            Transition.create_from_data(
                self.diff_state_high,
                self.state_low,
                partial_lifetime=0.1,
            )
        with self.assertRaises(TransitionError):
            Transition.create_from_data(
                self.state_high,
                self.diff_state_low,
                partial_lifetime=0.1,
            )
        with self.assertRaises(TransitionError):
            Transition.create_from_data(
                self.state_high,
                self.state_high,
                partial_lifetime=0.1,
            )
        _ = Transition.create_from_data(
            self.state_high, self.state_low, partial_lifetime=0.1
        )
        _ = Transition.create_from_data(
            self.diff_state_high,
            self.diff_state_low,
            partial_lifetime=0.1,
        )
        self.assertEqual(2, len(Transition.objects.all()))

    def test_delta_energy(self):
        t = Transition.create_from_data(
            self.state_high, self.state_low, partial_lifetime=0.1
        )
        self.assertEqual(t.delta_energy, self.state_low.energy - self.state_high.energy)

    def test_sync(self):
        t = Transition.create_from_data(
            self.state_high, self.state_low, partial_lifetime=0.1
        )
        s = State.create_from_data(
            self.isotopologue,
            lifetime=0.1,
            energy=42,
            vib_state_str="(9, 9, 9)",
            vib_state_labels="(v1, v2, v3)",
        )
        t.initial_state = s
        t.sync()
        t.save()
        self.assertEqual(t.delta_energy, -42.1)
        t = Transition.get_from_states(s, self.state_low)
        self.assertEqual(t.delta_energy, -42.1)

    def test_create_delete_transitions(self):
        self.assertEqual(self.isotopologue.number_transitions, 0)
        self.assertEqual(self.isotopologue.molecule.formula_str, "CO2")

        s1, s2, s3 = (
            self.state_high,
            self.state_low,
            State.create_from_data(
                self.isotopologue,
                lifetime=0.1,
                energy=42,
                vib_state_str="(9, 9, 9)",
                vib_state_labels="(v1, v2, v3)",
            ),
        )

        _ = Transition.create_from_data(s1, s2, 0)
        _ = Transition.create_from_data(s3, s2, 0)
        tr3 = Transition.create_from_data(s3, s1, 0)

        # direct create/save should change the Isotopologue.number_transitions etc
        for iso in Isotopologue.get_from_formula_str("CO2"), self.isotopologue:
            self.assertEqual(iso.number_transitions, Transition.objects.count())
        self.assertEqual(
            (s1.transition_from_set.count(), s1.number_transitions_from), (1, 1)
        )
        self.assertEqual(
            (s1.transition_to_set.count(), s1.number_transitions_to), (1, 1)
        )
        self.assertEqual(
            (s2.transition_from_set.count(), s2.number_transitions_from), (0, 0)
        )
        self.assertEqual(
            (s2.transition_to_set.count(), s2.number_transitions_to), (2, 2)
        )
        self.assertEqual(
            (s3.transition_from_set.count(), s3.number_transitions_from), (2, 2)
        )
        self.assertEqual(
            (s3.transition_to_set.count(), s3.number_transitions_to), (0, 0)
        )

        # direct delete should change the Isotopologue.number_transitions
        tr3.delete()
        iso = Isotopologue.get_from_formula_str("CO2")
        self.assertEqual(iso.number_transitions, Transition.objects.count())
        self.assertEqual(
            (s1.transition_from_set.count(), s1.number_transitions_from), (1, 1)
        )
        self.assertEqual(
            (s1.transition_to_set.count(), s1.number_transitions_to), (0, 0)
        )
        self.assertEqual(
            (s2.transition_from_set.count(), s2.number_transitions_from), (0, 0)
        )
        self.assertEqual(
            (s2.transition_to_set.count(), s2.number_transitions_to), (2, 2)
        )
        self.assertEqual(
            (s3.transition_from_set.count(), s3.number_transitions_from), (1, 1)
        )
        self.assertEqual(
            (s3.transition_to_set.count(), s3.number_transitions_to), (0, 0)
        )

        # indirect/batch delete/save sadly does not trigger the changes in number_
        # transitions in Isotopologue and States, I just could not make it work :(

    def test_update_state(self):
        s1 = State.create_from_data(
            self.isotopologue,
            lifetime=0.1,
            energy=1,
            vib_state_str="(1, 0, 0)",
            vib_state_labels="(v1, v2, v3)",
        )
        s2 = State.create_from_data(
            self.isotopologue,
            lifetime=0.1,
            energy=2,
            vib_state_str="(0, 2, 0)",
            vib_state_labels="(v1, v2, v3)",
        )
        s3 = State.create_from_data(
            self.isotopologue,
            lifetime=0.1,
            energy=3,
            vib_state_str="(0, 0, 3)",
            vib_state_labels="(v1, v2, v3)",
        )

        tr1_pk = Transition.create_from_data(s1, s2, 1).pk
        tr2_pk = Transition.create_from_data(s3, s2, 1).pk

        self.assertEqual(Transition.objects.get(pk=tr1_pk).delta_energy, 1)
        self.assertEqual(Transition.objects.get(pk=tr2_pk).delta_energy, -1)
        s2.energy = 42
        self.assertEqual(Transition.objects.get(pk=tr1_pk).delta_energy, 1)
        self.assertEqual(Transition.objects.get(pk=tr2_pk).delta_energy, -1)
        s2.save()
        self.assertEqual(Transition.objects.get(pk=tr1_pk).delta_energy, 41)
        self.assertEqual(Transition.objects.get(pk=tr2_pk).delta_energy, 39)
