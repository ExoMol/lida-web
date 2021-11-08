"""This needs to be run from the Django shell"""
from tqdm import tqdm

from app_site.models import Molecule, Isotopologue, State, Transition

for model in [Molecule, Isotopologue, State, Transition]:
    for instance in tqdm(model.objects.all()):
        instance.sync(verbose=True)
        instance.save()
