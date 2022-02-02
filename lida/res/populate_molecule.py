"""
Needs to be imported (not run!) from the Django shell...
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

file_dir = Path(__file__).parent.resolve().absolute()
res_dir = file_dir.parent.resolve().absolute()
if not str(res_dir) is sys.path:
    sys.path.append(str(res_dir))


if __name__ != '__main__':
    from app_site.models import Molecule, Isotopologue, State, Transition


def get_state_ground(states_dataframe):
    state_ground = states_dataframe.loc[np.isinf(states_dataframe['lifetime']), 'state']
    assert len(state_ground) == 1, 'Automatic determination of the ground electronic state failed!'
    return list(state_ground)[0]


if __name__ != '__main__':

    def populate_molecule(molecule_formula):

        try:
            isotopologue = Isotopologue.get_from_formula_str(molecule_formula)
        except Isotopologue.DoesNotExist:
            molecule_names = exomol_all.molecules[molecule_formula].names
            if len(molecule_names):
                name = molecule_names[0]
            else:
                name = ''
            molecule = Molecule.create_from_data(molecule_formula, name)
            iso_formula, dataset_name = molecules_info.loc[molecule_formula, ['iso_formula', 'dataset_name']]
            inchi_key = exomol_all.molecules[molecule_formula].isotopologues[iso_formula].inchi_key
            version = exomol_all.molecules[molecule_formula].isotopologues[iso_formula].version
            isotopologue = Isotopologue.create_from_data(
                molecule=molecule,
                iso_formula_str=iso_formula,
                inchi_key=inchi_key,
                dataset_name=dataset_name,
                version=version
            )

        states_df, transitions_df = get_data(molecule_formula)

        if len(isotopologue.state_set.all()) == 0:
            assert len(Transition.objects.filter(initial_state__isotopologue=isotopologue)) == 0, \
                'WARNING! Inconsistency!'
            states = {}  # django model instances
            print(f'Adding: States and transitions for {molecule_formula}.')
            for i in tqdm(states_df.index):
                el_state, vib_state, lifetime, energy = \
                    states_df.loc[i, ['state', 'vib_state', 'lifetime', 'energy']]
                if el_state and not isotopologue.ground_el_state_str:
                    isotopologue.set_ground_el_state_str(get_state_ground(states_df))
                state = State.create_from_data(isotopologue, float(lifetime), float(energy),
                                               el_state_str=el_state, vib_state_str=vib_state)
                states[(el_state, vib_state)] = state
            for i in tqdm(transitions_df.index):
                key0_i, key1_i, key0_f, key1_f, partial_lifetime, branching_ratio = \
                    transitions_df.loc[
                        i, ['state_i', 'vib_state_i', 'state_f', 'vib_state_f', 'partial_lifetime', 'branching_ratio']
                    ]
                initial_state = states[(key0_i, key1_i)]
                final_state = states[(key0_f, key1_f)]
                Transition.create_from_data(initial_state, final_state, float(partial_lifetime), float(branching_ratio))
            assert len(State.objects.filter(isotopologue=isotopologue)) == len(states_df)
            assert len(Transition.objects.filter(initial_state__isotopologue=isotopologue)) == len(transitions_df)
        elif len(isotopologue.state_set.all()) == len(states_df):
            assert len(Transition.objects.filter(initial_state__isotopologue=isotopologue)) == \
                   len(transitions_df), 'WARNING! Inconsistency!'
            print(f'States and transitions for {molecule_formula} probably added already? Check it!')
        else:
            raise ValueError('States already partially populated?')

if __name__ == '__main__':
    with pd.option_context('display.max_rows', None):
        for f in ['CO', 'SiH', 'SiH2', 'SiH4']:
            s_df, t_df = get_data(f)
            print(f'Ground state of {f}: {get_state_ground(s_df)}')
            print(s_df)
