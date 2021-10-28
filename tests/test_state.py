from django.test import TestCase
from pyvalem.state import StateParseError

from elida.apps.molecule.models import Molecule, Isotopologue
from elida.apps.state.exceptions import StateError
from elida.apps.state.models import State
from elida.apps.state.utils import validate_and_parse_vib_state_str, canonicalise_and_parse_el_state_str


class TestUtils(TestCase):
    def test_vib_state_str_valid(self):
        self.assertEqual(([], ''), validate_and_parse_vib_state_str(''))
        self.assertEqual(([0], '<i>v</i>=0'), validate_and_parse_vib_state_str('0'))
        self.assertEqual(([1], '<i>v</i>=1'), validate_and_parse_vib_state_str('1'))
        self.assertEqual(([456], '<i>v</i>=456'), validate_and_parse_vib_state_str('456'))
        self.assertEqual(
            ([1, 1, 1], '<b><i>v</i></b>=(1, 1, 1)'),
            validate_and_parse_vib_state_str('(1, 1, 1)')
        )
        self.assertEqual(
            ([0, 0, 5, 0], '<b><i>v</i></b>=(0, 0, 5, 0)'),
            validate_and_parse_vib_state_str('(0, 0, 5, 0)')
        )
        self.assertEqual(
            ([0, 0, 0], '<b><i>v</i></b>=(0, 0, 0)'),
            validate_and_parse_vib_state_str('(0, 0, 0)')
        )
        self.assertEqual(
            ([0, 0], '<b><i>v</i></b>=(0, 0)'),
            validate_and_parse_vib_state_str('(0, 0)')
        )

    def test_vib_state_str_invalid(self):
        illegal_arguments = [
            '-1', '(0, 1, -1)', '(-1, -1, -1)',
            '(0)', '(42)',
            '1, 1, 1', '(1, 0, 0', '0, 1, 1)', '(1,1,1)', '(1,  1, 1)',
        ]
        for arg in illegal_arguments:
            with self.subTest(arg=arg):
                with self.assertRaises(StateError):
                    validate_and_parse_vib_state_str(arg)

    def test_vib_state_str_illegal_type(self):
        illegal_arguments = [
            (1, 1, 1), 1, 0, (0, 0, 0),
        ]
        for arg in illegal_arguments:
            with self.subTest(arg=arg):
                with self.assertRaises(TypeError):
                    validate_and_parse_vib_state_str(arg)

    def test_el_state_canonicalisation(self):
        self.assertEqual('1Σ-', canonicalise_and_parse_el_state_str(' 1SIGMA- ')[0])


# noinspection PyTypeChecker
class TestState(TestCase):
    def setUp(self):
        self.molecule = Molecule.create_from_data(formula_str='CO2+', name='carbon dioxide ion')
        self.isotopologue = Isotopologue.create_from_data(self.molecule, iso_formula_str='(12C)(16O)2+',
                                                          inchi_key='inchi_key', dataset_name='name', version=1)
        self.isotopologue.set_ground_el_state_str('X(2PI)')
        self.isotopologue.set_vib_state_dim(3)

        self.diff_molecule = Molecule.create_from_data(formula_str='CO', name='carbon monoxide')
        self.diff_isotopologue = Isotopologue.create_from_data(self.diff_molecule, iso_formula_str='(12C)(16O)',
                                                               inchi_key='inchi_key', dataset_name='name',
                                                               version=1)
        self.diff_isotopologue.set_ground_el_state_str('X(2PI)')
        self.diff_isotopologue.set_vib_state_dim(1)

    def test_create_from_data(self):
        self.assertEqual(0, len(State.objects.all()))
        el_state_str_list = ['1SIGMA-', 'A(3PI)', 'a(1SIGMA-)']
        for iso, vib_state_str_list in zip(
                [self.isotopologue, self.diff_isotopologue],
                [['(0, 0, 0)', '(1, 2, 3)', '(0, 1, 0)'], ['1', '0', '42']]
        ):
            for el_state_str, vib_state_str in zip(el_state_str_list, vib_state_str_list):
                with self.subTest(isotopologue=iso, el_state_str=el_state_str, vib_state_str=vib_state_str):
                    State.create_from_data(iso, 0.42, 0.42, el_state_str=el_state_str, vib_state_str=vib_state_str)
        self.assertEqual(2 * len(el_state_str_list), len(State.objects.all()))

    def test_no_states(self):
        self.assertEqual(0, len(State.objects.all()))
        self.isotopologue.set_vib_state_dim(0)
        State.create_from_data(self.isotopologue, 0.42, 0.42, el_state_str='1SIGMA-')
        self.isotopologue.set_vib_state_dim(3)
        State.create_from_data(self.isotopologue, 0.42, 0.42, el_state_str='1SIGMA-', vib_state_str='(0, 1, 2)')
        self.isotopologue.set_vib_state_dim(3)
        self.isotopologue.set_ground_el_state_str('')
        State.create_from_data(self.isotopologue, 0.42, 0.42, vib_state_str='(0, 1, 2)')
        self.isotopologue.set_vib_state_dim(0)
        with self.assertRaises(StateError):
            State.create_from_data(self.isotopologue, 0.42, 0.42)
        self.assertEqual(len(State.objects.all()), 3)

    def test_create_from_data_invalid_state(self):
        self.assertEqual(0, len(State.objects.all()))
        with self.assertRaises(StateParseError):
            State.create_from_data(self.isotopologue, 0.42, 0.42, 'foo')
        with self.assertRaises(StateParseError):
            State.create_from_data(self.isotopologue, 0.42, 0.42, el_state_str='v=0')
        self.assertEqual(0, len(State.objects.all()))

    def test_create_from_data_invalid_values(self):
        self.assertEqual(0, len(State.objects.all()))
        self.isotopologue.set_ground_el_state_str('')
        with self.assertRaises(StateError):
            State.create_from_data(self.isotopologue, vib_state_str='(10, 10, 10)', lifetime=-0.1, energy=0.42)
        # negative energy allowed:
        _ = State.create_from_data(self.isotopologue, vib_state_str='(10, 10, 10)', lifetime=0.1, energy=-0.42)
        self.assertEqual(1, len(State.objects.all()))

    def test_create_from_data_attributes_1(self):
        self.assertEqual(0, len(State.objects.all()))
        s = State.create_from_data(self.isotopologue, vib_state_str='(2, 0, 1)', lifetime=0.42, energy=-0.42,
                                   el_state_str='1SIGMA-')
        self.assertEqual(self.isotopologue.pk, s.pk)
        self.assertEqual('(2, 0, 1)', s.vib_state_str)
        self.assertEqual('1Σ-', s.el_state_str)
        self.assertEqual(0.42, s.lifetime)
        self.assertEqual(-0.42, s.energy)
        self.assertEqual('<b><i>v</i></b>=(2, 0, 1)', s.vib_state_html)
        self.assertEqual('<sup>1</sup>Σ<sup>-</sup>', s.el_state_html)

    def test_create_from_data_duplicate(self):
        self.assertEqual(0, len(State.objects.all()))
        self.isotopologue.set_ground_el_state_str('')
        self.diff_isotopologue.set_ground_el_state_str('')
        State.create_from_data(self.isotopologue, vib_state_str='(0, 0, 0)', lifetime=0.42, energy=-0.42)
        with self.assertRaises(StateError):
            State.create_from_data(self.isotopologue, vib_state_str='(0, 0, 0)', lifetime=0, energy=0)
        State.create_from_data(self.isotopologue, vib_state_str='(1, 0, 0)', lifetime=0.42, energy=-0.42)
        State.create_from_data(self.diff_isotopologue, vib_state_str='2', lifetime=0.42, energy=-0.42)
        self.assertEqual(3, len(State.objects.all()))

    def test_create_from_data_canonicalization_duplicate(self):
        self.assertEqual(0, len(State.objects.all()))
        self.isotopologue.set_vib_state_dim(0)
        State.create_from_data(self.isotopologue, el_state_str='1SIGMA-', lifetime=0.42, energy=-0.42)
        for a in ['1SIGMA-', '1Σ-', ' 1Σ- ']:
            with self.assertRaises(StateError):
                State.create_from_data(self.isotopologue, el_state_str=a, lifetime=0, energy=0)
        self.assertEqual(1, len(State.objects.all()))

    def test_get_from_data(self):
        self.assertEqual(0, len(State.objects.all()))
        self.isotopologue.set_vib_state_dim(0)
        s = State.create_from_data(self.isotopologue, el_state_str='1SIGMA-', lifetime=0.42, energy=-0.42)
        self.assertEqual(1, len(State.objects.all()))
        self.assertEqual(s, State.get_from_data(self.isotopologue, el_state_str='1Σ-'))
        self.assertEqual(s, State.get_from_data(self.isotopologue, el_state_str=' 1Σ- '))
        self.assertEqual(s, State.get_from_data(self.isotopologue, el_state_str=' 1SIGMA- '))
        with self.assertRaises(State.DoesNotExist):
            State.get_from_data(self.diff_isotopologue, el_state_str='1Σ-')
        with self.assertRaises(State.DoesNotExist):
            State.get_from_data(self.isotopologue, el_state_str='3PI')
        self.assertEqual(1, len(State.objects.all()))

    def test_str(self):
        for iso in self.isotopologue, self.diff_isotopologue:
            iso.set_ground_el_state_str('')
        self.assertEqual('CO v=0', str(State.create_from_data(self.diff_isotopologue, 0, 0, vib_state_str='0')))
        self.assertEqual('CO v=1', str(State.create_from_data(self.diff_isotopologue, 0, 0, vib_state_str='1')))
        self.assertEqual('CO2+ v=(1,2,3)',
                         str(State.create_from_data(self.isotopologue, 0, 0, vib_state_str='(1, 2, 3)')))
        self.isotopologue.set_ground_el_state_str('X(2PI)')
        self.assertEqual('CO2+ a(2Π);v=(0,0,0)',
                         str(State.create_from_data(self.isotopologue, 0, 0, vib_state_str='(0, 0, 0)',
                                                    el_state_str='a(2PI)')))

    def test_repr(self):
        s = State.create_from_data(self.isotopologue, 0, 0, vib_state_str='(0, 1, 2)', el_state_str='1Σ-')
        self.assertEqual(f'{s.pk}:State(CO2+ 1Σ-;v=(0,1,2))', repr(s))

    def test_infinite_lifetime(self):
        self.isotopologue.set_ground_el_state_str('')
        s = State.create_from_data(self.isotopologue, vib_state_str='(0, 0, 0)', lifetime=float('inf'), energy=0)
        self.assertEqual(s.lifetime, None)
        s = State.create_from_data(self.isotopologue, vib_state_str='(0, 1, 2)', lifetime=None, energy=0)
        self.assertEqual(s.lifetime, None)
        s = State.create_from_data(self.isotopologue, vib_state_str='(10, 9, 8)', lifetime=42, energy=0)
        self.assertEqual(s.lifetime, 42)

    def test_auto_set_vib_dim(self):
        molecule = Molecule.create_from_data(formula_str='CO2', name='carbon dioxide')
        isotopologue = Isotopologue.create_from_data(molecule, iso_formula_str='(12C)(16O)2',
                                                     inchi_key='inchi_key', dataset_name='name', version=1)
        self.assertEqual(0, isotopologue.state_set.count())
        self.assertEqual(0, isotopologue.vib_state_dim)
        State.create_from_data(isotopologue, 0, 0, vib_state_str='(0, 0, 0)')
        self.assertEqual(3, isotopologue.vib_state_dim)
        with self.assertRaises(StateError):
            State.create_from_data(isotopologue, 0, 0, vib_state_str='1')
        with self.assertRaises(StateError):
            State.create_from_data(isotopologue, 0, 0, vib_state_str='(11, 1)')
        with self.assertRaises(StateError):
            State.create_from_data(isotopologue, 0, 0, vib_state_str='(11, 1, 5, 6)')
        State.create_from_data(isotopologue, 0, 0, vib_state_str='(1, 1, 1)')
        self.assertEqual(2, isotopologue.state_set.count())

    def test_invalid_vibrational_state_str(self):
        # prime the vib_dims:
        self.isotopologue.set_ground_el_state_str('')
        State.create_from_data(self.isotopologue, 0, 0, vib_state_str='(99, 99, 99)')
        self.diff_isotopologue.set_ground_el_state_str('')
        State.create_from_data(self.diff_isotopologue, 0, 0, vib_state_str='99')

        for iso, invalid_vib_str_list in zip(
                [self.isotopologue, self.diff_isotopologue],
                [
                    ['(0,0,0)', '(1,  2, 3)', '0, 1, 0)', '(0, 1, 0', '0, 0, 0', '(1., 2, 3)', '(00, 1, 1)', '(1, 1)',
                     ''],
                    ['(1)', '', '1.0', '(1', '2)', '1 ', ' 2']
                ]
        ):
            for vib_str in invalid_vib_str_list:
                with self.subTest(iso=iso, vib_str=vib_str):
                    with self.assertRaises(StateError):
                        State.create_from_data(iso, 0, 0, vib_state_str=vib_str)

    def test_ground_state(self):
        molecule = Molecule.create_from_data(formula_str='CO2', name='carbon dioxide')
        isotopologue = Isotopologue.create_from_data(molecule, iso_formula_str='(12C)(16O)2',
                                                     inchi_key='inchi_key', dataset_name='name', version=1)
        State.create_from_data(isotopologue, 0, 0, vib_state_str='(0, 0, 0)')
        with self.assertRaises(StateError):
            # cannot pass el state if no ground state defined in Isotopologue
            State.create_from_data(isotopologue, 0, 0, vib_state_str='(0, 0, 0)', el_state_str='1SIGMA-')
        isotopologue.set_ground_el_state_str('X(2PI)')
        with self.assertRaises(StateError):
            # must pass el state if ground state defined in Isotopologue
            State.create_from_data(isotopologue, 0, 0, vib_state_str='(0, 0, 0)')
        self.assertEqual(1, isotopologue.state_set.count())

    def test_state_html(self):
        s = State.create_from_data(self.isotopologue, 0, 0, el_state_str='1SIGMA-', vib_state_str='(1, 1, 1)')
        self.assertEqual(s.vib_state_str, '(1, 1, 1)')
        self.assertEqual(s.vib_state_html, '<b><i>v</i></b>=(1, 1, 1)')
        s = State.create_from_data(self.isotopologue, 0, 0, el_state_str='1SIGMA-', vib_state_str='(2, 0, 0)')
        self.assertEqual(s.vib_state_str, '(2, 0, 0)')
        self.assertEqual(s.vib_state_html, '<b><i>v</i></b>=(2, 0, 0)')
        s = State.create_from_data(self.isotopologue, 0, 0, el_state_str='1SIGMA-', vib_state_str='(0, 0, 0)')
        self.assertEqual(s.vib_state_str, '(0, 0, 0)')
        self.assertEqual(s.vib_state_html, '<b><i>v</i></b>=(0, 0, 0)')
        s = State.create_from_data(self.diff_isotopologue, 0, 0, el_state_str='1SIGMA-', vib_state_str='1')
        self.assertEqual(s.vib_state_str, '1')
        self.assertEqual(s.vib_state_html, '<i>v</i>=1')
        s = State.create_from_data(self.diff_isotopologue, 0, 0, el_state_str='1SIGMA-', vib_state_str='0')
        self.assertEqual(s.vib_state_str, '0')
        self.assertEqual(s.vib_state_html, '<i>v</i>=0')

    def test_vib_state_str_alt(self):
        s = State.create_from_data(self.isotopologue, 0, 0, el_state_str='1SIGMA-', vib_state_str='(1, 1, 1)')
        self.assertEqual(s.vib_state_str_alt, 'ν1+ν2+ν3')
        s = State.create_from_data(self.isotopologue, 0, 0, el_state_str='1SIGMA-', vib_state_str='(2, 0, 0)')
        self.assertEqual(s.vib_state_str_alt, '2ν1')
        s = State.create_from_data(self.isotopologue, 0, 0, el_state_str='1SIGMA-', vib_state_str='(0, 0, 0)')
        self.assertEqual(s.vib_state_str_alt, '')
        s = State.create_from_data(self.diff_isotopologue, 0, 0, el_state_str='1SIGMA-', vib_state_str='1')
        self.assertEqual(s.vib_state_str_alt, 'v=1')
        s = State.create_from_data(self.diff_isotopologue, 0, 0, el_state_str='1SIGMA-', vib_state_str='0')
        self.assertEqual(s.vib_state_str_alt, 'v=0')
