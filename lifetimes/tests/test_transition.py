from django.test import TestCase
import numpy as np

from lifetimes.models import Formula, Isotopologue, State, Transition


# Create your tests here.
# noinspection PyTypeChecker
class TestTransition(TestCase):
    def setUp(self):
        self.formula = Formula.create_from_data(formula_str='CO2', name='carbon dioxide')
        self.isotopologue = Isotopologue.create_from_data(self.formula, iso_formula_str='(12C)(16O)2',
                                                          inchi_key='inchi_key', dataset_name='name', version=1)
        self.state_high = State.create_from_data(self.isotopologue, 'v=1', lifetime=0.1, energy=0.1)
        self.state_low = State.create_from_data(self.isotopologue, 'v=0', lifetime=np.inf, energy=0.0)

        self.diff_formula = Formula.create_from_data(formula_str='CO', name='carbon monoxide')
        self.diff_isotopologue = Isotopologue.create_from_data(self.diff_formula, iso_formula_str='(12C)(16O)',
                                                               inchi_key='inchi_key', dataset_name='name', version=42)
        self.diff_state_high = State.create_from_data(self.isotopologue, 'v=2', lifetime=0.01, energy=0.2)
        self.diff_state_low = State.create_from_data(self.isotopologue, 'v=1', lifetime=0.1, energy=0.1)
