import requests

from pyvalem.formula import Formula as PVFormula

from preferred_isotopologues import isotopologues
from exomol_all import exomol_all


def get_relevant_def_file(molecule_str: str) -> str:
    molecule_slug = PVFormula(molecule_str).slug
    preferred_isotopologue = isotopologues[molecule_str]
    isotopologue = exomol_all.molecules[molecule_str].isotopologues[preferred_isotopologue]
    iso_slug = isotopologue.iso_slug
    dataset_name = isotopologue.dataset_name
    url = f'https://www.exomol.com/db/{molecule_slug}/{iso_slug}/{dataset_name}/{iso_slug}__{dataset_name}.def'
    response = requests.get(url)
    return response.text


def print_relevant_def_file(molecule_str: str) -> None:
    print(get_relevant_def_file(molecule_str))
