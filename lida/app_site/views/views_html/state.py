from django.urls import reverse
from django.views.generic import TemplateView

from app_site.models import Molecule
from .utils import Column, Order


class StateListView(TemplateView):
    template_name = 'site/datatable.html'
    extra_context = {'search_footer': True, 'length_change': True, 'initial_order': [Order(1, 'asc'), ]}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        mol = Molecule.objects.get(slug=self.kwargs['mol_slug'])

        context['title'] = f'{mol.slug} states'
        context['content_heading'] = f'States of {mol.html}'
        context['ajax_url'] = reverse('state-list-ajax', args=[mol.slug])
        context['columns'] = [
            Column('Electronic state', 'el_state_html', 0, mol.isotopologue.resolves_el, True, True, ''),
            Column('Vibrational state', 'vib_state_html', 1, mol.isotopologue.resolves_vib, True, True, ''),
            Column('Energy (eV)', 'energy', 2, True, False, False, ''),
            Column('Lifetime (s)', 'lifetime', 3, True, False, False, ''),
            Column('Transitions from', 'number_transitions_from', 4, True, False, False, ''),
            Column('Transitions to', 'number_transitions_to', 5, True, False, False, ''),
        ]

        return context
