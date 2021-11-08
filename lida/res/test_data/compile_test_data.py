"""
This script reads some selected data of TianTian's Masters output and turns them into standardized pd.DataFrames
ready to be added to the Lida database.
Unfortunately, TianTian's outputs as they are are not very well standardized and also resolve some finer structures
than necessary and do not normalize the partial lifetimes.
The dataframes coming from this script should adhere to the following standard:

* States
  * Columns:
    * 'state': Electronic state as a pyvalem-valid molecular term symbol, or '', where not resolved.
               Examples: A(2Δ), B(2Σ+), X(2Π), a(4Σ+)
    * 'vib_state': Vibrational state in the form of a number (diatomic) or a vector.
                   Examples: 'v', '(v1, v2, v3)', '(v1, v2, v3, v4, v5, v6)', ... These are strings with int values
    * 'energy': Float
    * 'lifetime': Float
  * No duplicate states! Each pair of 'state', 'vib_state' must be unique in the dataframe.
  * At least one value in the 'lifetime' column should be float('inf') denoting the ground state.
* Transitions
  * Columns:
    * 'state_i': Must be present in States DataFrame
    * 'vib_state_i': Must be present in States DataFrame
    * 'state_f': Must be present in States DataFrame
    * 'vib_state_f': Must be present in States DataFrame
    * 'partial_lifetime': Float, sum of one initial to all final must be normalized to States['lifetime']
    * 'branching_ratio': Float, sum of one initial to all final must be normalized to 1
  * No duplicate transitions! Each vector ['state_i', 'vib_state_i', 'state_f', 'vib_state_f'] must be unique.
  * Each pair of ['state_i', 'vib_state_i'] as well as each pair of ['state_f', 'vib_state_f'] must be present in
    the States dataframe!
"""

from pathlib import Path

import numpy as np
import pandas as pd

file_dir = Path(__file__).parent.resolve().absolute()
res_dir = file_dir.parent.resolve().absolute()


def parse_state(state_series: pd.Series, formula: str) -> pd.DataFrame:
    res = pd.DataFrame(index=state_series.index, columns=['state', 'vib_state'])
    if formula == 'CO':
        res['state'] = ''
        res['vib_state'] = [state[1:-1] for state in state_series]
    elif formula == 'SiH2':
        res['state'] = ''
        res['vib_state'] = [f'({state[1:-1]})' for state in state_series]
    elif formula == 'SiH':
        state_map = {'A2Delta': 'A(2DELTA)', 'B2Sigma': 'B(2SIGMA+)', 'X2Pi': 'X(2PI)', 'a4Sigma': 'a(4SIGMA+)'}
        for i in state_series.index:
            state_str = state_series[i]
            states = state_str.lstrip('[').rstrip(']').split(', ')
            state, vib_state, _, _, _ = states
            res.loc[i] = state_map[state.strip("'")], vib_state
    elif formula == 'SiH4':
        res['state'] = ''
        for i in state_series.index:
            states = state_series[i].lstrip('[').rstrip(']').split(', ')
            v1, v2, _, v3, _, _, v4, _, _ = states
            res.loc[i, 'vib_state'] = f'({v1}, {v2}, {v3}, {v4})'
    else:
        assert False
    return res


def get_states(formula):
    df_raw = pd.read_csv(file_dir / 'tiantian_selected_results' / f'{formula}_states.csv', header=0)
    df = pd.DataFrame(index=df_raw.index, columns='state vib_state energy lifetime'.split())
    if formula == 'CO':
        state_col = "['v']"
    elif formula == 'SiH':
        state_col = "['State', 'v', 'Lambda', 'Sigma', 'Omega']"
    elif formula == 'SiH2':
        state_col = "['v1', 'v2', 'v3']"
    elif formula == 'SiH4':
        state_col = "['n1', 'n2', 'L2', 'n3', 'L3', 'M3', 'n4', 'L4', 'M4']"
    else:
        assert False
    df.loc[:, ['state', 'vib_state']] = parse_state(df_raw[state_col], formula)
    df['energy'] = sorted(np.random.random(len(df)))  # dummy data
    df['lifetime'] = df_raw['lifetime_i']

    # lump duplicate states but preserve the ground state:
    ground = df.loc[df['lifetime'] == float('inf'), ['state', 'vib_state']]
    g_state, g_vib_state = ground.iloc[0]
    df = df.drop_duplicates(['state', 'vib_state']).reset_index(drop=True)
    g_mask = (df['state'] == g_state) & (df['vib_state'] == g_vib_state)
    df.loc[g_mask, 'lifetime'] = float('inf')
    assert sum(np.isinf(df['lifetime']))
    return df


def get_transitions(formula, states, normalize=True):
    df_raw = pd.read_csv(file_dir / 'tiantian_selected_results' / f'{formula}_transitions.csv', header=0)
    df = pd.DataFrame(index=df_raw.index,
                      columns='state_i vib_state_i state_f vib_state_f partial_lifetime branching_ratio'.split())
    df[['state_i', 'vib_state_i']] = parse_state(df_raw['initial_state'], formula)
    df[['state_f', 'vib_state_f']] = parse_state(df_raw['final_state'], formula)
    df['branching_ratio'] = df_raw.loc[:, 'branching_ratio']
    df['partial_lifetime'] = df_raw.loc[:, 'lifetime']
    # prune duplicate transitions:
    df.drop_duplicates('state_i vib_state_i state_f vib_state_f'.split(), inplace=True)
    # drop the states which are not present in the states dataframe:
    set_states = set(str(a) for a in states['state'])
    set_vib_states = set(str(a) for a in states['vib_state'])
    mask1a = pd.Series([a in set_states for a in df['state_i']], index=df.index)
    mask1b = pd.Series([a in set_vib_states for a in df['vib_state_i']], index=df.index)
    mask2a = pd.Series([a in set_states for a in df['state_f']], index=df.index)
    mask2b = pd.Series([a in set_vib_states for a in df['vib_state_f']], index=df.index)
    mask = (mask1a & mask1b) & (mask2a & mask2b)
    df = df.loc[mask]
    # drop the transitions with identical initial and final states:
    mask1 = df['state_i'] == df['state_f']
    mask2 = df['vib_state_i'] == df['vib_state_f']
    df = df.loc[~(mask1 & mask2)]
    df.reset_index(drop=True, inplace=True)
    if normalize:
        normalize_transitions(states, df)
    return df


def normalize_transitions(states_df, transitions_df):
    for i in states_df.index:
        if np.isinf(states_df.loc[i, 'lifetime']):
            continue
        state, vib_state = states_df.loc[i, ['state', 'vib_state']]
        a_tot = 1 / states_df.loc[i, 'lifetime']
        trans_i = transitions_df.loc[
            (transitions_df['state_i'] == state) & (transitions_df['vib_state_i'] == vib_state)
            ]
        a_i = 1 / trans_i['partial_lifetime']
        lifetime_factor = a_tot / sum(a_i)
        branching_factor = 1 / sum(trans_i['branching_ratio'])
        assert sum(a_i) > 0, f'{states_df.loc[i]}'
        mask = (transitions_df['state_i'] == state) & (transitions_df['vib_state_i'] == vib_state)
        transitions_df.loc[mask, 'partial_lifetime'] /= lifetime_factor
        transitions_df.loc[mask, 'branching_ratio'] *= branching_factor


def get_data(formula):
    states = get_states(formula)
    transitions = get_transitions(formula, states)
    return states, transitions


if __name__ == '__main__':
    # for f in ['SiH2']:
    for f in ['CO', 'SiH', 'SiH2', 'SiH4']:
        s = get_states(f)
        print(s)
        print(get_transitions(f, s, normalize=True))
