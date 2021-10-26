from django.test import TestCase
from elida.apps.state.utils import parse_and_validate_vib_state_str, canonicalise_el_state_str
from elida.apps.state.exceptions import StateError
from pyvalem.state import StateParseError
from elida.apps.molecule.models import Molecule, Isotopologue
from elida.apps.state.models import State


class TestUtils(TestCase):
    def test_vib_state_str_valid(self):
        self.assertEqual((0, '', ''), parse_and_validate_vib_state_str(''))
        self.assertEqual((1, '<i>v</i>=0', '<i>v</i>=0'), parse_and_validate_vib_state_str('0'))
        self.assertEqual((1, '<i>v</i>=1', '<i>v</i>=1'), parse_and_validate_vib_state_str('1'))
        self.assertEqual((1, '<i>v</i>=456', '<i>v</i>=456'), parse_and_validate_vib_state_str('456'))
        self.assertEqual(
            (3, 'ν<sub>1</sub> + ν<sub>2</sub> + ν<sub>3</sub>', '<b><i>v</i></b>=(1, 1, 1)'),
            parse_and_validate_vib_state_str('(1, 1, 1)')
        )
        self.assertEqual(
            (4, '5ν<sub>3</sub>', '<b><i>v</i></b>=(0, 0, 5, 0)'),
            parse_and_validate_vib_state_str('(0, 0, 5, 0)')
        )
        self.assertEqual(
            (3, '<b><i>v</i></b>=<b>0</b>', '<b><i>v</i></b>=<b>0</b>'),
            parse_and_validate_vib_state_str('(0, 0, 0)')
        )
        self.assertEqual(
            (2, '<b><i>v</i></b>=<b>0</b>', '<b><i>v</i></b>=<b>0</b>'),
            parse_and_validate_vib_state_str('(0, 0)')
        )

    def test_vib_state_str_invalid(self):
        illegal_arguments = [
            '-1', '(0, 1, -1)', '(-1, -1, -1)',
            '(0)', '(42)',
            '1, 1, 1', '(1, 0, 0', '0, 1, 1)', '(1,1,1)', '(1,  1, 1)',
            # (1, 1, 1), 1, 0, (0, 0, 0),
        ]
        for arg in illegal_arguments:
            with self.subTest(arg=arg):
                with self.assertRaises(StateError):
                    parse_and_validate_vib_state_str(arg)

    def test_vib_state_str_illegal_type(self):
        illegal_arguments = [
            (1, 1, 1), 1, 0, (0, 0, 0),
        ]
        for arg in illegal_arguments:
            with self.subTest(arg=arg):
                with self.assertRaises(TypeError):
                    parse_and_validate_vib_state_str(arg)

    def test_el_state_canonicalisation(self):
        self.assertEqual('1Σ-', canonicalise_el_state_str(' 1SIGMA- '))


# # noinspection PyTypeChecker
# class TestState(TestCase):
#     def setUp(self):
#         self.molecule = Molecule.create_from_data(formula_str='CO2+', name='carbon dioxide ion')
#         self.isotopologue = Isotopologue.create_from_data(self.molecule, iso_formula_str='(12C)(16O)2+',
#                                                           inchi_key='inchi_key', dataset_name='name', version=1)
#         self.diff_molecule = Molecule.create_from_data(formula_str='CO', name='carbon monoxide')
#         self.diff_isotopologue = Isotopologue.create_from_data(self.diff_molecule, iso_formula_str='(12C)(16O)',
#                                                                inchi_key='inchi_key', dataset_name='name',
#                                                                version=1)
#
#     def test_create_from_data(self):
#         self.assertEqual(0, len(State.objects.all()))
#         el_state_str_list = ['1SIGMA-', '', '1SIGMA-']
#         vib_state_str_list = ['', 'v=5', '3v1+2v5']
#         for el_state_str, vib_state_str in zip(el_state_str_list, vib_state_str_list):
#             State.create_from_data(self.isotopologue, 0.42, 0.42,
#                                    el_state_str=el_state_str, vib_state_str=vib_state_str)
#         self.assertEqual(len(el_state_str_list), len(State.objects.all()))
#
#     def test_no_states(self):
#         self.assertEqual(0, len(State.objects.all()))
#         State.create_from_data(self.isotopologue, 0.42, 0.42, el_state_str='1SIGMA-')
#         State.create_from_data(self.isotopologue, 0.42, 0.42, vib_state_str='v=0')
#         with self.assertRaises(ValueError):
#             State.create_from_data(self.isotopologue, 0.42, 0.42)
#         self.assertEqual(len(State.objects.all()), 2)
#
#     def test_create_from_data_invalid_state(self):
#         self.assertEqual(0, len(State.objects.all()))
#         with self.assertRaises(StateParseError):
#             State.create_from_data(self.isotopologue, 0.42, 0.42, 'foo')
#         with self.assertRaises(StateParseError):
#             State.create_from_data(self.isotopologue, 0.42, 0.42, el_state_str='v=0')
#         self.assertEqual(0, len(State.objects.all()))
#
#     def test_create_from_data_invalid_values(self):
#         self.assertEqual(0, len(State.objects.all()))
#         with self.assertRaises(ValueError):
#             State.create_from_data(self.isotopologue, vib_state_str='v=0', lifetime=-0.1, energy=0.42)
#         # negative energy allowed:
#         _ = State.create_from_data(self.isotopologue, vib_state_str='v=0', lifetime=0.1, energy=-0.42)
#         self.assertEqual(1, len(State.objects.all()))
#
#     def test_create_from_data_attributes(self):
#         self.assertEqual(0, len(State.objects.all()))
#         s = State.create_from_data(self.isotopologue, vib_state_str='1v3+2v1', lifetime=0.42, energy=-0.42)
#         self.assertEqual(self.isotopologue.pk, s.pk)
#         self.assertEqual('2ν1+ν3', s.vib_state_str)
#         self.assertEqual('', s.el_state_str)
#         self.assertEqual(0.42, s.lifetime)
#         self.assertEqual(-0.42, s.energy)
#         self.assertEqual('2ν<sub>1</sub> + ν<sub>3</sub>', s.vib_state_html)
#         self.assertEqual('', s.el_state_html)
#
#     def test_create_from_data_duplicate(self):
#         self.assertEqual(0, len(State.objects.all()))
#         State.create_from_data(self.isotopologue, vib_state_str='v=0', lifetime=0.42, energy=-0.42)
#         with self.assertRaises(ValueError):
#             State.create_from_data(self.isotopologue, vib_state_str='v=0', lifetime=0, energy=0)
#         State.create_from_data(self.isotopologue, vib_state_str='v=1', lifetime=0.42, energy=-0.42)
#         State.create_from_data(self.diff_isotopologue, vib_state_str='v=0', lifetime=0.42, energy=-0.42)
#         self.assertEqual(3, len(State.objects.all()))
#
#     def test_create_from_data_canonicalization_duplicate(self):
#         self.assertEqual(0, len(State.objects.all()))
#         State.create_from_data(self.isotopologue, vib_state_str='v1+3v3', el_state_str='1SIGMA-',
#                                lifetime=0.42, energy=-0.42)
#         for b, a in zip(['3v3+v1', '1v1+3v3', 'ν1+3ν3'],
#                         ['1SIGMA-', '1Σ-', '1Σ-']):
#             with self.assertRaises(ValueError):
#                 State.create_from_data(self.isotopologue, el_state_str=a, vib_state_str=b, lifetime=0, energy=0)
#         self.assertEqual(1, len(State.objects.all()))
#
#     def test_get_from_data(self):
#         self.assertEqual(0, len(State.objects.all()))
#         s = State.create_from_data(self.isotopologue, el_state_str='1SIGMA-', lifetime=0.42, energy=-0.42)
#         self.assertEqual(1, len(State.objects.all()))
#         self.assertEqual(s, State.get_from_data(self.isotopologue, el_state_str='1Σ-'))
#         with self.assertRaises(State.DoesNotExist):
#             State.get_from_data(self.diff_isotopologue, el_state_str='1Σ-')
#         with self.assertRaises(State.DoesNotExist):
#             State.get_from_data(self.isotopologue, el_state_str='3PI')
#         self.assertEqual(1, len(State.objects.all()))
#
#     def test_canonicalise_el_state_str(self):
#         state = '1SIGMA-'
#         for alternative_state in ['1Σ-']:
#             self.assertEqual(State.canonicalise_state_str(state, 'el'),
#                              State.canonicalise_state_str(alternative_state, 'el'))
#
#     def test_canonicalise_vib_state_str(self):
#         state = 'v1+v3'
#         for alternative_state in ['1v1+1v3', '1v3+v1', 'ν1+ν3']:
#             self.assertEqual(State.canonicalise_state_str(state, 'vib'),
#                              State.canonicalise_state_str(alternative_state, 'vib'))
#
#     def test_str(self):
#         self.assertEqual('CO (v=0)', str(State.create_from_data(self.diff_isotopologue, 0, 0, vib_state_str='v=0')))
#         self.assertEqual('CO (v=1)', str(State.create_from_data(self.diff_isotopologue, 0, 0, vib_state_str='v=1')))
#         self.assertEqual('CO', str(State.create_from_data(self.diff_isotopologue, 0, 0)))
#         self.assertEqual('CO2+ (ν1+2ν2+3ν3)', str(State.create_from_data(self.isotopologue,
#                                                                          0, 0, vib_state_str='1v1+2v2+3v3')))
#         self.assertEqual('CO2+', str(State.create_from_data(self.isotopologue, 0, 0)))
#
#     def test_repr(self):
#         s = State.create_from_data(self.isotopologue, 'v=0', 0, 0)
#         self.assertEqual(f'{s.pk}:State(CO2+ (v=0))', repr(s))
#         s = State.create_from_data(self.isotopologue, '', 0, 0)
#         self.assertEqual(f'{s.pk}:State(CO2+)', repr(s))
#
#     def test_infinite_lifetime(self):
#         s = State.create_from_data(self.isotopologue, state_str='v=0', lifetime=float('inf'), energy=0)
#         self.assertEqual(s.lifetime, None)
#         s = State.create_from_data(self.isotopologue, state_str='v=2', lifetime=None, energy=0)
#         self.assertEqual(s.lifetime, None)
#         s = State.create_from_data(self.isotopologue, state_str='v=1', lifetime=42, energy=0)
#         self.assertEqual(s.lifetime, 42)
