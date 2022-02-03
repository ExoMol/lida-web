from django.test import TestCase
from pyvalem.formula import FormulaParseError
from pyvalem.states.molecular_term_symbol import MolecularTermSymbolError

from ..models import Molecule, Isotopologue
from ..models.exceptions import MoleculeError


# noinspection PyTypeChecker
class TestIsotopologue(TestCase):
    def setUp(self):
        self.molecule = Molecule.objects.create(
            formula_str="CO", name="name", html="html", charge=0, number_atoms=2
        )
        self.test_attributes = {
            "id": 42,
            "iso_formula_str": "(12C)(16O)",
            "iso_slug": "",
            "dataset_name": "",
            "version": 1,
            "html": "",
            "mass": 1,
            "number_states": 0,
            "number_transitions": 0,
        }

    def test_create_from_data(self):
        self.assertEqual(0, len(Isotopologue.objects.all()))
        Isotopologue.create_from_data(
            self.molecule, iso_formula_str="(12C)(16O)", dataset_name="", version=1
        )
        self.assertEqual(1, len(Isotopologue.objects.all()))

    def test_create_from_data_duplicate(self):
        self.assertEqual(0, len(Isotopologue.objects.all()))
        _ = Isotopologue.create_from_data(
            self.molecule, iso_formula_str="(12C)(16O)", dataset_name="", version=1
        )
        self.assertEqual(1, len(Isotopologue.objects.all()))
        # same formula, different isotopologue formula (not allowed):
        with self.assertRaises(MoleculeError):
            Isotopologue.create_from_data(
                self.molecule, iso_formula_str="(13C)(17O)", dataset_name="", version=1
            )
        # same isotopologue formula, different formula (not allowed):
        with self.assertRaises(MoleculeError):
            new_m = Molecule.objects.create(
                formula_str="CO2", name="name", html="html", charge=0, number_atoms=3
            )
            Isotopologue.create_from_data(
                new_m, iso_formula_str="(12C)(16O)", dataset_name="", version=1
            )

        # both different, no problem!
        Isotopologue.create_from_data(
            new_m, iso_formula_str="(12C)2(16O)", dataset_name="", version=1
        )
        self.assertEqual(2, len(Isotopologue.objects.all()))

    def test_create_from_data_invalid(self):
        with self.assertRaises(FormulaParseError):
            Isotopologue.create_from_data(
                self.molecule,
                iso_formula_str="(12C)-foo-(16O)",
                dataset_name="",
                version=1,
            )

    def test_get_from_formula_str(self):
        with self.assertRaises(Isotopologue.DoesNotExist):
            Isotopologue.get_from_formula_str("CO")
        i1 = Isotopologue.objects.create(molecule=self.molecule, **self.test_attributes)
        i2 = Isotopologue.get_from_formula_str("CO")
        self.assertEqual(i1, i2)

    def test_get_from_iso_formula_str(self):
        with self.assertRaises(Isotopologue.DoesNotExist):
            Isotopologue.get_from_iso_formula_str("(12C)(16O)")
        i1 = Isotopologue.objects.create(molecule=self.molecule, **self.test_attributes)
        i2 = Isotopologue.get_from_iso_formula_str("(12C)(16O)")
        self.assertEqual(i1, i2)

    def test_html_iso_slug(self):
        i = Isotopologue.create_from_data(
            molecule=self.molecule,
            iso_formula_str="(12C)(16O)",
            dataset_name="",
            version=1,
        )
        self.assertEqual(i.html, "<sup>12</sup>C<sup>16</sup>O")
        self.assertEqual(i.iso_slug, "12C-16O")

    def test_time_added(self):
        i = Isotopologue.objects.create(molecule=self.molecule, **self.test_attributes)
        self.assertIsNot(None, i.time_added)

    def test_str(self):
        i = Isotopologue.objects.create(molecule=self.molecule, **self.test_attributes)
        self.assertEqual(str(i), "CO")

    def test_repr(self):
        i = Isotopologue.objects.create(molecule=self.molecule, **self.test_attributes)
        self.assertEqual(repr(i), "42:Isotopologue(CO)")

    def test_set_ground_state(self):
        i = Isotopologue.objects.create(molecule=self.molecule, **self.test_attributes)
        self.assertEqual("", i.ground_el_state_str)
        i.set_ground_el_state_str("1SIGMA-")
        self.assertEqual(i.ground_el_state_str, "1Σ-")
        with self.assertRaises(MolecularTermSymbolError):
            i.set_ground_el_state_str("FOO")
        self.assertEqual(i.ground_el_state_str, "1Σ-")
        i.set_ground_el_state_str("3PI")
        self.assertEqual(i.ground_el_state_str, "3Π")

    def test_validate_vib_state_dim(self):
        i = Isotopologue.objects.create(molecule=self.molecule, **self.test_attributes)
        self.assertEqual(i._validate_vib_state_dim(1), 1)
        with self.assertRaises(MoleculeError):
            i._validate_vib_state_dim(2)
        with self.assertRaises(MoleculeError):
            i._validate_vib_state_dim(-1)

    def test_split_vib_quantum_labels(self):
        self.assertEqual(Isotopologue._split_vib_quantum_labels("v"), ["v"])
        self.assertEqual(
            Isotopologue._split_vib_quantum_labels("(v1, v2, v3)"), ["v1", "v2", "v3"]
        )
        self.assertEqual(
            Isotopologue._split_vib_quantum_labels("(n1, n2, n3, n4)"),
            ["n1", "n2", "n3", "n4"],
        )
        self.assertEqual(
            Isotopologue._split_vib_quantum_labels("(v1, v2lin, v3)"),
            ["v1", "v2lin", "v3"],
        )

    def test_get_vib_quantum_labels_html(self):
        i = Isotopologue.objects.create(molecule=self.molecule, **self.test_attributes)
        self.assertEqual("", i.vib_quantum_labels_html)
        self.assertEqual(i._get_vib_quantum_labels_html(["v"]), "v")
        self.assertEqual(i._get_vib_quantum_labels_html(["v2"]), "v<sub>2</sub>")
        self.assertEqual(
            i._get_vib_quantum_labels_html(["v1", "v2", "n3"]),
            "(v<sub>1</sub>, v<sub>2</sub>, n<sub>3</sub>)",
        )
        self.assertEqual(
            i._get_vib_quantum_labels_html(["v1", "v2lin"]),
            "(v<sub>1</sub>, v<sub>2</sub><sup>lin</sup>)",
        )

    def test_set_vib_quantum_labels(self):
        i = Isotopologue.objects.create(molecule=self.molecule, **self.test_attributes)
        self.assertEqual("", i.vib_quantum_labels)
        self.assertEqual(0, i.vib_state_dim)
        self.assertEqual("", i.vib_quantum_labels_html)
        i.set_vib_quantum_labels("v")
        self.assertEqual(i.vib_state_dim, 1)
        self.assertEqual(i.vib_quantum_labels, "v"),
        self.assertNotEqual(i.vib_quantum_labels_html, "")
        i.molecule.number_atoms = 3
        i.set_vib_quantum_labels("(v1, v2, v3)")
        self.assertEqual(i.vib_state_dim, 3)
        self.assertEqual(i.vib_quantum_labels, "(v1, v2, v3)"),
        i.molecule.number_atoms = 4
        i.set_vib_quantum_labels("(v1,v2lin,v3,n4)")
        self.assertEqual(i.vib_state_dim, 4)
        self.assertEqual(i.vib_quantum_labels, "(v1,v2lin,v3,n4)"),

    def test_sync(self):
        i = Isotopologue.create_from_data(
            self.molecule, iso_formula_str="(12C)(16O)", dataset_name="", version=1
        )
        i.iso_formula_str = "(1H)2(16O)+"
        i.sync()
        self.assertEqual("", i.dataset_name)
        self.assertEqual("<sup>1</sup>H<sub>2</sub><sup>16</sup>O<sup>+</sup>", i.html)
        self.assertEqual(i.iso_slug, "1H2-16O_p")
