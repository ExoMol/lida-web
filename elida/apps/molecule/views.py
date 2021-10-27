from django.views.generic import ListView, DetailView

from .models import Molecule


class MoleculeDetailView(DetailView):
    model = Molecule
    template_name = 'molecule_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'{context["object"].slug} details'
        return context


class MoleculeListView(ListView):
    model = Molecule
    template_name = 'molecule_list.html'
    extra_context = {'title': 'Molecules', 'datatable_class': 'molecule-table'}
