from django.views.generic import ListView
from .models import State
from elida.apps.molecule.models import Molecule


class StateListView(ListView):
    template_name = 'state_list.html'

    def get_queryset(self):
        return State.objects.filter(isotopologue__molecule__slug=self.kwargs['mol_slug'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mol = Molecule.objects.get(slug=self.kwargs['mol_slug'])
        mol_html = mol.html
        context['table_heading'] = f'States of {mol_html}'
        context['title'] = f'{mol.slug} states'
        context['resolves_el'] = mol.isotopologue.resolves_el()
        context['resolves_vib'] = mol.isotopologue.resolves_vib()
        return context
