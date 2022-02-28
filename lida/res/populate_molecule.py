"""
Needs to be imported from the Django shell...
"""
import json
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from app_site.models import Molecule, Isotopologue, State, Transition


def populate_molecule(processed_data_dir):
    """
    This is a high-level function to populate a single molecule data to the database.

    It needs to be run from within the Django shell. It requires as an argument a
    path towards a directory which has been previously created by the `exomol2lida`
    package, and it expects all the data files created by `exomol2lida`.
    The lida-web project is very much interconnected and dependent on `exomol2lida`.

    Parameters
    ----------
    processed_data_dir : str or Path
        Path towards the contents of the `exomol2lida` processing and post-processing
        outputs for this molecule. The `exomol2lida` is a separate repo, containing
        the code to generate inputs for the LIDA database.
        The directory NEEDS to be named with the molecular formula, exactly as
        logged by the `exomol2lida.process_dataset.DatasetProcessor`.
    """

    processed_data_dir = Path(processed_data_dir)
    molecule_formula = processed_data_dir.name
    with open(processed_data_dir / "meta_data.json") as fp:
        dataset_metadata = json.load(fp)

    try:
        isotopologue = Isotopologue.get_from_formula_str(molecule_formula)
        if isotopologue.state_set.count() or isotopologue.transition_set.count():
            raise ValueError(
                f"The isotopologue {isotopologue} already has some states or "
                f"transitions attached. These need to be removed for the automated "
                f"population script to run."
            )

    except Isotopologue.DoesNotExist:
        # create molecule and isotopologue
        molecule = Molecule.create_from_data(molecule_formula)
        iso_formula = dataset_metadata["iso_formula"]
        dataset_name = dataset_metadata["input"]["dataset_name"]
        version = dataset_metadata["version"]
        isotopologue = Isotopologue.create_from_data(
            molecule=molecule,
            iso_formula_str=iso_formula,
            dataset_name=dataset_name,
            version=version,
        )

    if processed_data_dir.joinpath("states_electronic_raw.csv").is_file():
        if not processed_data_dir.joinpath("states_electronic.csv").is_file():
            raise ValueError(
                f"ABORTING {molecule_formula} population: The data need to be "
                f"post-processed by exomol2lida (states_electronic_raw.csv is "
                f"not translated to states_electronic.csv)!"
            )

    # load in all the states and transitions data as dataframes:
    states_el, states_vib, vib_state_labels = None, None, None
    el_state_str, vib_state_str, vib_state_labels = "", "", ""
    if processed_data_dir.joinpath("states_electronic.csv").is_file():
        states_el = pd.read_csv(
            processed_data_dir / "states_electronic.csv", header=0, index_col=0
        )
    if processed_data_dir.joinpath("states_vibrational.csv").is_file():
        states_vib = pd.read_csv(
            processed_data_dir / "states_vibrational.csv", header=0, index_col=0
        )
    if states_vib is not None:
        vib_state_labels = f"({', '.join(states_vib.columns)})"

    states_data = pd.read_csv(
        processed_data_dir / "states_data.csv", header=0, index_col=0
    )
    transitions_data = pd.read_csv(
        processed_data_dir / "transitions_data.csv", header=0
    )

    if states_el is not None:
        # electronic states are resolved, need to set the state_string for the
        # ground state - just take the state with the lowest energy.
        i = states_data.sort_values(by="E").index[0]
        ground_el_state_str = states_el.loc[i, "State"]
        isotopologue.set_ground_el_state_str(ground_el_state_str)

    state_instances = {}  # django model instances
    print(f"Adding: States and transitions for {molecule_formula}.")
    for i in tqdm(states_data.index):
        lifetime, energy = states_data.loc[i, ["tau", "E"]]
        if states_el is not None:
            el_state_str = states_el.loc[i, "State"]
        if states_vib is not None:
            vib_state = tuple(states_vib.loc[i])
            if len(vib_state) == 1:
                vib_state = vib_state[0]
            vib_state_str = str(vib_state)
        state = State.create_from_data(
            isotopologue=isotopologue,
            lifetime=float(lifetime),
            energy=float(energy),
            el_state_str=el_state_str,
            vib_state_labels=vib_state_labels,
            vib_state_str=vib_state_str,
        )
        state_instances[i] = state

    for j in tqdm(transitions_data.index):
        i, f, tau_if = transitions_data.loc[j, ["i", "f", "tau_if"]]
        Transition.create_from_data(
            initial_state=state_instances[i],
            final_state=state_instances[f],
            partial_lifetime=float(tau_if)
        )
    assert State.objects.filter(isotopologue=isotopologue).count() == len(states_data)
    assert Transition.objects.filter(
        initial_state__isotopologue=isotopologue
    ).count() == len(transitions_data)
