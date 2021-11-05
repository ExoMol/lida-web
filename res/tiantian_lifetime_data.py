from pathlib import Path

import pandas as pd

lifetimes_project_root = Path('/home/martin/Downloads/vibrational_lifetime-main')


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
    df.column_names = [col if col != 'linelist' else 'dataset_name' for col in df.column_names]
    assert len(df.index) == len(set(df.index))
    return df


molecules_info = get_computed_molecules_info()

if __name__ == '__main__':
    # with pd.option_context('display.max_rows', None):
    print(molecules_info)
