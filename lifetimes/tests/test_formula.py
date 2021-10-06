import pyvalem.formula
from django.test import TestCase

from lifetimes.models import Formula


# Create your tests here.
# noinspection PyTypeChecker
class TestFormula(TestCase):
    def test_create_from_str(self):
        self.assertEqual(len(Formula.objects.all()), 0)
        Formula.create_from_data('CO2+', name='carbon dioxide ion')
        self.assertEqual(len(Formula.objects.all()), 1)
        f = Formula.objects.get(formula_str='CO2+')
        self.assertEqual(f.charge, 1)
        self.assertEqual(f.html, 'CO<sub>2</sub><sup>+</sup>')
        self.assertEqual(f.natoms, 3)
        self.assertEqual(f.name, 'carbon dioxide ion')

    def test_invalid_formula_str(self):
        with self.assertRaises(pyvalem.formula.FormulaError):
            Formula.create_from_data('Foo', name='Foo')
        self.assertEqual(len(Formula.objects.all()), 0)

    def test_get_from_formula_str(self):
        with self.assertRaises(Formula.DoesNotExist):
            Formula.get_from_formula_str('CO')
        Formula.create_from_data('CO', 'carbon monoxide')
        f = Formula.get_from_formula_str('CO')
        self.assertEqual(f.name, 'carbon monoxide')
        self.assertEqual(len(Formula.objects.all()), 1)

    def test_time_added(self):
        self.assertIsNot(None, Formula.create_from_data('CO', 'CO').time_added)

    def test_str(self):
        f = Formula.create_from_data('CO2+', 'carbon monoxide')
        self.assertEqual('CO2+', str(f))

    def test_repr(self):
        f = Formula.objects.create(formula_str='CO', name='', html='', charge=0, natoms=2, id=42)
        self.assertEqual(f.id, 42)
        self.assertEqual('42:Formula(CO)', repr(f))
