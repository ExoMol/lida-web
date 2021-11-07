from django.views.generic import ListView

from .models import Molecule


class MoleculeListView(ListView):
    model = Molecule
    template_name = 'molecule_list.html'
    extra_context = {'title': 'Molecules', 'content_heading': 'Molecules'}
