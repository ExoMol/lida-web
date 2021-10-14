"""
Needs to be imported (not run!) from the Django shell...
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm import tqdm

file_root = Path(__file__).parent.resolve().absolute()
res_root = file_root.parent.resolve().absolute()
if not str(res_root) is sys.path:
    sys.path.append(str(res_root))

# noinspection PyUnresolvedReferences
import context

from res.test_data.compile_test_data import get_data
from res.exomol_all import exomol_all
from res.tiantian_lifetime_data import molecules_info

if __name__ != '__main__':
    from lifetimes.models import Formula, Isotopologue, State, Transition


def get_state_ground(states_dataframe):
    state_ground = states_dataframe.loc[np.isinf(states_dataframe['lifetime']), 'state']
    assert len(state_ground) == 1
    return list(state_ground)[0]


def add_state_strings(states_dataframe):
    """This is to compile pyvalem-valid state strings out of the electronic and vibrational state strings taken out
    of the standardized dataframes describing the states and transitions of an ExoMol linelist.
    The results are added as a column to the passed states dataframe.
    """
    state_ground = get_state_ground(states_dataframe)
    states_dataframe['state_pyvalem'] = ''
    for i in states_dataframe.index:
        state, vib_state = states_dataframe.loc[i, ['state', 'vib_state']]

        if state != state_ground:
            states_dataframe.at[i, 'state_pyvalem'] = state

        vib_quanta = [int(v.strip()) for v in vib_state.lstrip('[').rstrip(']').split(',')]
        if len(vib_quanta) == 1:
            if vib_quanta[0] > 0:
                vib_str = f'v={vib_quanta[0]}'
            else:
                vib_str = ''
        else:
            vib_str = ''
            for num, quantum in enumerate(vib_quanta, start=1):
                if quantum > 0:
                    vib_str += f'{quantum}v{num}+'
            vib_str = vib_str.rstrip('+')
        states_dataframe.at[i, 'state_pyvalem'] = \
            f"{states_dataframe.at[i, 'state_pyvalem']};{vib_str}".strip('; ')


if __name__ != '__main__':

    def add_data_to_elida(molecule_formula):

        try:
            isotopologue = Isotopologue.get_from_formula_str(molecule_formula)
        except Isotopologue.DoesNotExist:
            molecule_names = exomol_all.molecules[molecule_formula].names
            if len(molecule_names):
                name = molecule_names[0]
            else:
                name = ''
            formula = Formula.create_from_data(molecule_formula, name)
            iso_formula, dataset_name = molecules_info.loc[molecule_formula, ['iso_formula', 'dataset_name']]
            inchi_key = exomol_all.molecules[molecule_formula].isotopologues[iso_formula].inchi_key
            version = exomol_all.molecules[molecule_formula].isotopologues[iso_formula].version
            isotopologue = Isotopologue.create_from_data(
                formula=formula,
                iso_formula_str=iso_formula,
                inchi_key=inchi_key,
                dataset_name=dataset_name,
                version=version
            )

        states_df, transitions_df = get_data(molecule_formula)
        add_state_strings(states_df)

        if len(isotopologue.state_set.all()) == 0:
            assert len(Transition.objects.filter(initial_state__isotopologue=isotopologue)) == 0, \
                'WARNING! Inconsistency!'
            states = {}  # django model instances
            print(f'Adding: States and transitions for {molecule_formula}.')
            for i in tqdm(states_df.index):
                key0, key1, state_str, lifetime, energy = \
                    states_df.loc[i, ['state', 'vib_state', 'state_pyvalem', 'lifetime', 'energy']]
                state = State.create_from_data(isotopologue, state_str, float(lifetime), float(energy))
                states[(key0, key1)] = state
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
            add_state_strings(s_df)
            print(s_df)
