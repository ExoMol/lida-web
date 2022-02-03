import pyvalem.formula
from django.test import TestCase

from ..models import Molecule
from ..models.exceptions import MoleculeError


# Create your tests here.
# noinspection PyTypeChecker
class TestMolecule(TestCase):
    def test_create_from_str(self):
        self.assertEqual(len(Molecule.objects.all()), 0)
        Molecule.create_from_data("CO2+", name="carbon dioxide ion")
        self.assertEqual(len(Molecule.objects.all()), 1)
        f = Molecule.objects.get(formula_str="CO2+")
        self.assertEqual(f.charge, 1)
        self.assertEqual(f.html, "CO<sub>2</sub><sup>+</sup>")
        self.assertEqual(f.number_atoms, 3)
        self.assertEqual(f.name, "carbon dioxide ion")

    def test_invalid_formula_str(self):
        with self.assertRaises(pyvalem.formula.FormulaError):
            Molecule.create_from_data("Foo", name="Foo")
        self.assertEqual(len(Molecule.objects.all()), 0)

    def test_get_from_formula_str(self):
        with self.assertRaises(Molecule.DoesNotExist):
            Molecule.get_from_formula_str("CO")
        Molecule.create_from_data("CO", "carbon monoxide")
        f = Molecule.get_from_formula_str("CO")
        self.assertEqual(f.name, "carbon monoxide")
        self.assertEqual(len(Molecule.objects.all()), 1)

    def test_time_added(self):
        self.assertIsNot(None, Molecule.create_from_data("CO", "CO").time_added)

    def test_str(self):
        f = Molecule.create_from_data("CO2+", "carbon monoxide")
        self.assertEqual("CO2+", str(f))

    def test_repr(self):
        f = Molecule.objects.create(
            formula_str="CO", name="", html="", charge=0, number_atoms=2, id=42
        )
        self.assertEqual(f.id, 42)
        self.assertEqual("42:Molecule(CO)", repr(f))

    def test_create_duplicate(self):
        Molecule.create_from_data("CO", "foo")
        with self.assertRaises(MoleculeError):
            Molecule.create_from_data("CO", "boo")
        Molecule.create_from_data("CO2", "foo")
        self.assertEqual(2, len(Molecule.objects.all()))

    def test_html(self):
        f = Molecule.create_from_data("CO2+", "carbon monoxide")
        self.assertEqual("CO<sub>2</sub><sup>+</sup>", f.html)

    def test_sync(self):
        m = Molecule.create_from_data("CO2+", name="carbon dioxide ion")
        self.assertEqual(m.html, "CO<sub>2</sub><sup>+</sup>")
        self.assertEqual(m.charge, 1)
        m.formula_str = "CO"
        self.assertEqual(m.html, "CO<sub>2</sub><sup>+</sup>")
        self.assertEqual(m.charge, 1)
        m.sync()
        self.assertEqual(m.html, "CO")
        self.assertEqual(m.charge, 0)
        self.assertEqual(m.slug, "CO")
        self.assertEqual(m.number_atoms, 2)

        m.formula_str = "H2O-"
        m.sync(sync_only=["slug"])
        self.assertEqual(m.html, "CO")
        self.assertEqual(m.charge, 0)
        self.assertEqual(m.slug, "H2O_m")
        self.assertEqual(m.number_atoms, 2)
