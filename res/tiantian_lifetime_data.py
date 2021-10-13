"""This needs to be executed from within the django shell!!"""

import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

lifetimes_project_root = Path('/home/martin/Downloads/vibrational_lifetime-main')
res_root = Path(__file__).parent.absolute().resolve()
sys.path.append(str(res_root))
from exomol_all import exomol_all

# django imports:
if not __name__ == '__main__':
    from lifetimes.models import Formula, Isotopologue, State, Transition


def get_computed_molecules_info():
    df = pd.read_csv(lifetimes_project_root / 'linelist.csv', header=0, index_col=0)
    for mol_lab in df.index:
        compute_info_path = lifetimes_project_root / 'compute_info' / f'{mol_lab}.csv'
        try:
            with open(compute_info_path, 'r') as f:
                lines = list(f.readlines())
            last = lines[-1]
            assert last.startswith(mol_lab), (mol_lab, last)
            state_labels = last.split('[')[1].split(']')[0].replace("'", '')
            df.loc[mol_lab, 'state_labels'] = f'[{state_labels}]'
        except FileNotFoundError:
            continue

    df = df.loc[df['state_labels'].notna()]
    df.index = list(df.index)
    # add formulas
    df.index = [a[:-2] + '+' if a.endswith('_p') else a for a in df.index]
    df = df.drop(columns=['iso_slug'])

    # rename the columns:
    df.columns = [col if col != 'linelist' else 'dataset_name' for col in df.columns]
    assert len(df.index) == len(set(df.index))
    return df


molecules_info = get_computed_molecules_info()


# noinspection PyUnusedLocal
def parse_state(molecule_formula, state_raw, state_label):
    states = state_raw.lstrip('[').rstrip(']').split(',')
    states = [s.strip() for s in states]
    if state_label == '[v]':
        assert state_label == molecules_info.at[molecule_formula, 'state_labels']
        if states[0] == '0':
            return ''
        return f'v={states[0]}'
    elif state_label in {'[v1, v2]', '[v1, v2, v3]', '[v1, v2, v3, v4, v5, v6]'}:
        assert state_label == molecules_info.at[molecule_formula, 'state_labels']
        labels = state_label.lstrip('[').rstrip(']').split(',')
        labels = [lab.strip() for lab in labels]
        states = [int(float(s)) for s in states]
        state_strings = []
        for quant, lab in zip(states, labels):
            if int(quant) != 0:
                state_strings.append(f'{quant}{lab}')
        return '+'.join(state_strings)  # returns '' for 0v1+0v2+0v3!
    else:
        raise NotImplementedError(f"Unknown state label: '{state_label}'")


def get_states_info(molecule_formula):
    paths = list(lifetimes_project_root.joinpath('v3_result').glob(molecule_formula.replace('+', '_p') + '_v3*.csv'))
    if molecule_formula in {'CS', 'PN', 'SiH2'}:
        # here, two paths exist, will take the last one (sorted by the datetime)!
        pass
    elif molecule_formula == 'SiO':
        paths = list(lifetimes_project_root.joinpath('v3_result').glob('SiO_v3_23-08-2021.csv'))
    else:
        assert len(paths) == 1
    path = sorted(paths)[-1]
    df = pd.read_csv(str(path), header=0)
    state_label = df.columns[0]
    state_label = str(state_label).replace("'", '')
    # TODO: try state_label = molecules_info.at[molecule_formula, 'state_labels']
    df['state_label'] = state_label
    df.columns = ['state_raw', 'lifetime', 'state_label']
    df['state_raw'] = [a.replace("'", '') for a in df['state_raw']]
    df['state'] = [parse_state(molecule_formula, state_raw, state_label) for state_raw in df['state_raw']]
    df['energy'] = 0
    return df


def get_transitions_info(molecule_formula):
    f = molecule_formula.replace('+', '_p')
    paths = list(lifetimes_project_root.joinpath('decay_result', f, 'v3').glob(f'{f}_*.csv'))
    if molecule_formula in {'CS', 'PN', 'SiH2'}:
        # here, two paths exist, will take the last one (sorted by the datetime)!
        pass
    elif molecule_formula == 'SiO':
        paths = list(lifetimes_project_root.joinpath('decay_result', f, 'v3').glob('SiO_23-08-2021.csv'))
    else:
        assert len(paths) == 1
    path = sorted(paths)[-1]
    df = pd.read_csv(path, header=0)
    assert list(df.columns)[:2] == ['initial_state', 'final_state']
    df.columns = ['initial_state_raw', 'final_state_raw'] + list(df.columns)[2:]
    df['initial_state_raw'] = [a.replace("'", '') for a in df['initial_state_raw']]
    df['final_state_raw'] = [a.replace("'", '') for a in df['final_state_raw']]

    # some states in the transition tables do not correspond with the ones in the states tables:
    # TODO: I need to fully understand these and treat them, currently they are just ignored!
    if molecule_formula == 'H2O':
        df = df.loc[df['final_state_raw'] != '[-2, -2, -2]']
    if molecule_formula == 'H3+':
        df = df.loc[df['final_state_raw'] != '[-1, -1]']
        df = df.loc[df['final_state_raw'] != '[2, 1]']  # this state is not defined! Why?

    state_label = molecules_info.at[molecule_formula, 'state_labels']
    df['initial_state'] = [parse_state(molecule_formula, a, state_label) for a in df['initial_state_raw']]
    df['final_state'] = [parse_state(molecule_formula, a, state_label) for a in df['final_state_raw']]

    return df


if not __name__ == '__main__':
    def add_data_to_elida(molecule_formula):

        states_info = get_states_info(molecule_formula)
        transitions_info = get_transitions_info(molecule_formula)

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

        if len(isotopologue.state_set.all()) == 0:
            assert len(Transition.objects.filter(initial_state__isotopologue=isotopologue)) == 0, \
                'WARNING! Inconsistency!'
            states = {}
            print(f'Adding: States and transitions for {molecule_formula}.')
            for i in tqdm(states_info.index):
                state_str, lifetime, energy = states_info.loc[i, ['state', 'lifetime', 'energy']]
                state = State.create_from_data(isotopologue, state_str, float(lifetime), float(energy))
                states[states_info.at[i, 'state']] = state
            for i in tqdm(transitions_info.index):
                ini, fin, partial_lifetime, branching_ratio = \
                    transitions_info.loc[i, ['initial_state', 'final_state', 'lifetime', 'branching_ratio']]
                initial_state = states[ini]
                final_state = states[fin]
                Transition.create_from_data(initial_state, final_state, float(partial_lifetime), float(branching_ratio))
            assert len(State.objects.filter(isotopologue=isotopologue)) == len(states_info)
            assert len(Transition.objects.filter(initial_state__isotopologue=isotopologue)) == len(transitions_info)
        elif len(isotopologue.state_set.all()) == len(states_info):
            assert len(Transition.objects.filter(initial_state__isotopologue=isotopologue)) == \
                   len(transitions_info), 'WARNING! Inconsistency!'
            print(f'States and transitions for {molecule_formula} probably added already? Check it!')
        else:
            raise ValueError('States already partially populated?')


    def add_all_data_to_elida():
        print(f'Adding data for all the molecules: {list(molecules_info.index)}')
        for molecule_formula in molecules_info.index:
            try:
                add_data_to_elida(molecule_formula)
            except NotImplementedError as e:
                print(f'{molecule_formula} error: {e}')


if __name__ == '__main__':
    # with pd.option_context('display.max_rows', None):
    print(molecules_info)
    mol = 'H2O'
    print(get_states_info(mol))
    print(get_transitions_info(mol))
