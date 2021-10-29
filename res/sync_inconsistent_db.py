"""This needs to be run from the Django shell"""
from tqdm import tqdm

from elida.apps.molecule.models import Molecule, Isotopologue
from elida.apps.state.models import State
from elida.apps.transition.models import Transition

kwargs = {
    'molecule': {'verbose': True, 'propagate': False},
    'isotopologue': {'verbose': True},
    'state': {'verbose': True, 'propagate': False},
    'transition': {'verbose': True},
}

for model, model_name in zip([Molecule, Isotopologue, State, Transition],
                             ['molecule', 'isotopologue', 'state', 'transition']):
    for instance in tqdm(model.objects.all()):
        instance.sync(**kwargs[model_name])
        instance.save()
