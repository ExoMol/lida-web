from __future__ import annotations

from context import res_root

import warnings
from dataclasses import dataclass

import requests


# noinspection PyTypeHints
@dataclass
class ExomolAll:
    id: str
    version: str
    num_molecules: int
    num_isotopologues: int
    num_datasets: int
    molecules: list[Molecule]


# noinspection PyTypeHints
@dataclass
class Molecule:
    num_names: int
    names: list[str]
    formula: str
    num_isotopologues: int
    isotopologues: list[Isotopologue]


@dataclass
class Isotopologue:
    inchi_key: str
    iso_slug: str
    iso_formula: str
    dataset_name: str
    version: str


def get_exomol_all_raw() -> str:
    return requests.get('https://www.exomol.com/db/exomol.all').text


def parse_exomol_all(exomol_all_raw: str) -> ExomolAll:
    # noinspection PyTypeHints
    def parse_line(expected_comment) -> str:
        while True:
            line = lines.pop(0)
            line_num = n - len(lines)
            if line:
                break
            else:
                warnings.warn(f'Empty line detected on line {line_num}!')
        try:
            val, comment = line.split('# ')
        except ValueError:
            raise AssertionError(f'Inconsistency detected on line {line_num}!')
        assert comment == expected_comment, f'Inconsistent comment detected on line {line_num}!'
        return val.strip()

    lines = exomol_all_raw.split('\n')
    n = len(lines)

    exomol_id = parse_line('ID')

    all_version = parse_line('Version number with format YYYYMMDD')

    num_molecules = parse_line('Number of molecules in the database')
    num_molecules = int(num_molecules)
    molecules = []

    num_all_isotopologues = parse_line('Number of isotopologues in the database')
    num_all_isotopologues = int(num_all_isotopologues)
    all_isotopologues = []

    num_all_datasets = parse_line('Number of datasets in the database')
    num_all_datasets = int(num_all_datasets)
    all_datasets = set()

    molecules_with_duplicate_isotopologues = []

    # loop over molecules:
    for _ in range(num_molecules):
        num_names = parse_line('Number of molecule names listed')
        num_names = int(num_names)
        names = []

        # loop over the molecule names:
        for __ in range(num_names):
            name = parse_line('Name of the molecule')
            names.append(name)

        assert num_names == len(names)

        formula = parse_line('Molecule chemical formula')

        num_isotopologues = parse_line('Number of isotopologues considered')
        num_isotopologues = int(num_isotopologues)
        isotopologues = []

        # loop over the isotopologues:
        for __ in range(num_isotopologues):
            inchi_key = parse_line('Inchi key of isotopologue')
            iso_slug = parse_line('Iso-slug')
            iso_formula = parse_line('IsoFormula')
            dataset_name = parse_line('Isotopologue dataset name')
            version = parse_line('Version number with format YYYYMMDD')

            isotopologue = Isotopologue(inchi_key, iso_slug, iso_formula, dataset_name, version)
            isotopologues.append(isotopologue)

            all_datasets.add(dataset_name)
            all_isotopologues.append(isotopologue)

        assert num_isotopologues == len(isotopologues)

        # check if all the isotopologues are in fact different (only a single dataset should be recommended):
        if len(isotopologues) != len(set(isotopologue.iso_formula for isotopologue in isotopologues)):
            molecules_with_duplicate_isotopologues.append(formula)

        molecule = Molecule(num_names, names, formula, num_isotopologues, isotopologues)
        molecules.append(molecule)

    # final assertions:
    if len(molecules_with_duplicate_isotopologues):
        # warnings.warn(f'Molecules with duplicate isotopologues detected: {molecules_with_duplicate_isotopologues}')
        raise AssertionError(f'Molecules with duplicate isotopologues detected: '
                             f'{molecules_with_duplicate_isotopologues}')

    assert num_molecules == len(molecules)

    if num_all_isotopologues != len(all_isotopologues):
        # warnings.warn(f'Number of isotopologues stated ({num_all_isotopologues}) does not match the actual number '
        #               f'({len(all_isotopologues)})!')
        raise AssertionError(f'Number of isotopologues stated ({num_all_isotopologues}) does not match the actual '
                             f'number ({len(all_isotopologues)})!')

    # if num_all_datasets != len(all_datasets):
    #     # warnings.warn(f'Number of datasets stated ({num_all_datasets}) does not match the actual number '
    #     #               f'({len(all_datasets)})!')
    #     raise AssertionError(f'Number of datasets stated ({num_all_datasets}) does not match the actual number '
    #                          f'({len(all_datasets)})!')

    return ExomolAll(exomol_id, all_version, num_molecules, num_all_isotopologues, num_all_datasets, molecules)


if __name__ == '__main__':

    with open(res_root / 'exomol_all_fixed.txt', 'r') as f:
        all_raw = str(f.read())

    # all_raw = get_exomol_all_raw()

    exomol_all = parse_exomol_all(all_raw)
