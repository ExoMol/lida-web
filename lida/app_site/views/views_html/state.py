from django.urls import reverse
from django.views.generic import TemplateView

from app_site.models import Molecule
from .utils import Column, Order


class StateListView(TemplateView):
    template_name = 'site/datatable.html'
    extra_context = {'table_footer': True, 'initial_order': [Order(1)], 'scroller': True}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        mol = Molecule.objects.get(slug=self.kwargs['mol_slug'])

        context['title'] = f'{mol.slug} states'
        context['content_heading'] = f'States of {mol.html}'
        context['ajax_url'] = reverse('state-list-ajax', args=[mol.slug])
        context['datatable_id'] = f'datatable-state-{mol.slug}'
        context['columns'] = [
            Column('Electronic state', 'el_state_html', 0,
                   visible=mol.isotopologue.resolves_el, searchable=True, individual_search=True),
            Column('Vibrational state', 'vib_state_html', 1,
                   visible=mol.isotopologue.resolves_vib, searchable=True, individual_search=True),
            Column('Energy (eV)', 'energy', 2),
            Column('Lifetime (s)', 'lifetime', 3),
            Column('Transitions from', 'number_transitions_from', 4),
            Column('Transitions to', 'number_transitions_to', 5),
        ]

        return context
