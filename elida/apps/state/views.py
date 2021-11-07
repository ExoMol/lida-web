from collections import namedtuple

from django.views.generic import TemplateView
from .models import State
from elida.apps.molecule.models import Molecule
from django_datatables_serverside.views import ServerSideDataTableView
from django.urls import reverse


Column = namedtuple('Column', 'heading model_field index visible searchable individual_search')
Order = namedtuple('Order', 'index dir')


class StateListView(TemplateView):
    template_name = 'datatable.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        mol = Molecule.objects.get(slug=self.kwargs['mol_slug'])

        context['title'] = f'{mol.slug} states'
        context['content_heading'] = f'States of {mol.html}'
        context['search_footer'] = True
        context['ajax_url'] = reverse('state-list-ajax', args=[mol.slug])
        context['length_change'] = True
        context['columns'] = [
            Column('Electronic state', 'el_state_html', 0, mol.isotopologue.resolves_el(), True, True),
            Column('Vibrational state', 'vib_state_html', 1, mol.isotopologue.resolves_vib(), True, True),
            Column('Energy (eV)', 'energy', 2, True, False, False),
            Column('Lifetime (s)', 'lifetime', 3, True, False, False),
            Column('Transitions from', 'number_transitions_from', 4, True, False, False),
            Column('Transitions to', 'number_transitions_to', 5, True, False, False),
        ]
        context['initial_order'] = [Order(1, 'asc'), ]

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
