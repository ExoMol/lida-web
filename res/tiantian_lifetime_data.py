"""This needs to be executed from within the django shell!!"""

import sys
from pathlib import Path

import pandas as pd

lifetimes_project_root = Path('/home/martin/Downloads/vibrational_lifetime-main')
res_root = Path(__file__).parent.absolute().resolve()
sys.path.append(str(res_root))
from exomol_all import exomol_all

# # django imports:
# from lifetimes.models import Formula, Isotopologue, State


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
            df.loc[mol_lab, 'state_labels'] = state_labels
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


def get_states_info(molecule_formula):
    paths = list(lifetimes_project_root.joinpath('v3_result').glob(molecule_formula.replace('+', '_p') + '_v3*.csv'))
    assert len(paths) == 1
    path = paths[0]
    df = pd.read_csv(str(path), header=0)
    state_label = df.columns[0]
    df['state_label'] = str(state_label).replace("'", '')
    df.columns = ['state_raw', 'lifetime', 'state_label']
    df['state_raw'] = [a.replace("'", '') for a in df['state_raw']]
    return df


def get_transitions_info(molecule_formula):
    raise NotImplementedError


# def add_data_to_elida(molecule_formula):
#     try:
#         isotopologue = Isotopologue.get_from_formula_str(molecule_formula)
#     except Isotopologue.DoesNotExist:
#         molecule_names = exomol_all.molecules[molecule_formula].names
#         if len(molecule_names):
#             name = molecule_names[0]
#         else:
#             name = ''
#         formula = Formula.create_from_data(molecule_formula, name)
#         iso_formula, dataset_name = molecules_info.loc[molecule_formula, ['iso_formula', 'dataset_name']]
#         inchi_key = exomol_all.molecules[molecule_formula].isotopologues[iso_formula].inchi_key
#         version = exomol_all.molecules[molecule_formula].isotopologues[iso_formula].version
#         isotopologue = Isotopologue.create_from_data(
#             formula=formula,
#             iso_formula_str=iso_formula,
#             inchi_key=inchi_key,
#             dataset_name=dataset_name,
#             version=version
#         )
#     state_labels = molecules_info.at[molecule_formula, 'state_labels']
#     if state_labels == 'v':
#         pass
#     else:
#         raise NotImplementedError


if __name__ == '__main__':
    with pd.option_context('display.max_rows', None):
        print(get_states_info('SiH'))
        # print(molecules_info)
