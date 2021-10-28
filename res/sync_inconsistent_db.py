"""This needs to be run from the Django shell"""
from tqdm import tqdm

from elida.apps.molecule.models import Molecule, Isotopologue
from elida.apps.state.models import State
from elida.apps.transition.models import Transition

for model in Molecule, Isotopologue, State, Transition:
    for instance in tqdm(model.objects.all()):
        instance.sync(verbose=True, propagate=False)
