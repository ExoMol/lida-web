from django.test import TestCase
from pyvalem.formula import FormulaParseError

from lifetimes.models import Formula, Isotopologue


# Create your tests here.
# noinspection PyTypeChecker
class TestIsotopologue(TestCase):
    def setUp(self):
        self.formula = Formula.objects.create(formula_str='CO', name='name', html='html', charge=0, natoms=2)
        self.test_attributes = {'id': 42, 'iso_formula_str': '(12C)(16O)', 'iso_slug': '', 'inchi_key': '',
                                'dataset_name': '', 'version': 1, 'html': '', 'mass': 1}

    def test_create_from_data(self):
        self.assertEqual(0, len(Isotopologue.objects.all()))
        Isotopologue.create_from_data(self.formula, iso_formula_str='(12C)(16O)', inchi_key='', dataset_name='',
                                      version=1)
        self.assertEqual(1, len(Isotopologue.objects.all()))

    def test_create_from_data_duplicate(self):
        self.assertEqual(0, len(Isotopologue.objects.all()))
        _ = Isotopologue.create_from_data(self.formula, iso_formula_str='(12C)(16O)', inchi_key='', dataset_name='',
                                          version=1)
        self.assertEqual(1, len(Isotopologue.objects.all()))
        # same formula, different isotopologue formula (not allowed):
        with self.assertRaises(ValueError):
            Isotopologue.create_from_data(self.formula, iso_formula_str='(13C)(17O)', inchi_key='', dataset_name='',
                                          version=1)
        # same isotopologue formula, different formula (not allowed):
        with self.assertRaises(ValueError):
            new_f = Formula.objects.create(formula_str='CO2', name='name', html='html', charge=0, natoms=3)
            Isotopologue.create_from_data(new_f, iso_formula_str='(12C)(16O)', inchi_key='', dataset_name='', version=1)

        # both different, no problem!
        Isotopologue.create_from_data(new_f, iso_formula_str='(12C)2(16O)', inchi_key='', dataset_name='', version=1)
        self.assertEqual(2, len(Isotopologue.objects.all()))

    def test_create_from_data_invalid(self):
        with self.assertRaises(FormulaParseError):
            Isotopologue.create_from_data(self.formula, iso_formula_str='(12C)-foo-(16O)', inchi_key='',
                                          dataset_name='', version=1)

    def test_get_from_formula_str(self):
        with self.assertRaises(Isotopologue.DoesNotExist):
            Isotopologue.get_from_formula_str('CO')
        i1 = Isotopologue.objects.create(formula=self.formula, **self.test_attributes)
        i2 = Isotopologue.get_from_formula_str('CO')
        self.assertEqual(i1, i2)

    def test_get_from_iso_formula_str(self):
        with self.assertRaises(Isotopologue.DoesNotExist):
            Isotopologue.get_from_iso_formula_str('(12C)(16O)')
        i1 = Isotopologue.objects.create(formula=self.formula, **self.test_attributes)
        i2 = Isotopologue.get_from_iso_formula_str('(12C)(16O)')
        self.assertEqual(i1, i2)

    def test_html_iso_slug(self):
        i = Isotopologue.create_from_data(formula=self.formula, iso_formula_str='(12C)(16O)', inchi_key='',
                                          dataset_name='', version=1)
        self.assertEqual(i.html, '<sup>12</sup>C<sup>16</sup>O')
        self.assertEqual(i.iso_slug, '12C-16O')

    def test_time_added(self):
        i = Isotopologue.objects.create(formula=self.formula, **self.test_attributes)
        self.assertIsNot(None, i.time_added)

    def test_str(self):
        i = Isotopologue.objects.create(formula=self.formula, **self.test_attributes)
        self.assertEqual(str(i), 'CO')

    def test_repr(self):
        i = Isotopologue.objects.create(formula=self.formula, **self.test_attributes)
        self.assertEqual(repr(i), '42:Isotopologue(CO)')
