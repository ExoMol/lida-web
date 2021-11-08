from django.urls import reverse
from django.views.generic import TemplateView
from django_datatables_serverside.views import ServerSideDataTableView

from elida.apps.molecule.models import Molecule
from elida.apps.state.utils import Column, Order
from .models import State


class StateListView(TemplateView):
    template_name = 'datatable.html'
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


def number_transitions_from_value(instance):
    val = instance.number_transitions_from
    if not val:
        return ''
    href = reverse('transition-list-from-state', args=[instance.pk])
    cls = 'elida-link'
    return f'<a href="{href}" class="{cls}">{val}</a>'


def number_transitions_to_value(instance):
    val = instance.number_transitions_to
    if not val:
        return ''
    href = reverse('transition-list-to-state', args=[instance.pk])
    cls = 'elida-link'
    return f'<a href="{href}" class="{cls}">{val}</a>'


class StateDataTableAjaxView(ServerSideDataTableView):
    surrogate_columns_search = {'el_state_html': 'el_state_html_notags', 'vib_state_html': 'vib_state_html_notags'}
    surrogate_columns_sort = {'vib_state_html': 'vib_state_sort_key'}
    custom_value_getters = {
        'energy': lambda instance: f'{instance.energy:.3f}',
        'lifetime': lambda instance: f'{instance.lifetime:.2e}' if instance.lifetime is not None else '∞',
        'number_transitions_from': number_transitions_from_value,
        'number_transitions_to': number_transitions_to_value
    }

    @property
    def queryset(self):
        return State.objects.filter(isotopologue__molecule__slug=self.kwargs['mol_slug']).all()
