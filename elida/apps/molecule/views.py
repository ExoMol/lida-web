from django.shortcuts import render
from django.views.generic import ListView, DetailView

from .models import Molecule


class MoleculeDetailView(DetailView):
    model = Molecule
    template_name = 'molecule_detail.html'
    extra_context = {'title': 'Molecule'}


class MoleculeListView(ListView):
    model = Molecule
    template_name = 'molecule_list.html'
    paginate_by = 20
    extra_context = {'title': 'Molecules'}
