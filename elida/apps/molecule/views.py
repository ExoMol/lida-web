from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView
from django_datatables_serverside.views import ServerSideDataTableView
from django.template.loader import render_to_string

from elida.apps.state.utils import Column, Order
from .models import Molecule


class MoleculeListView(TemplateView):
    template_name = 'datatable.html'
    extra_context = {
        'title': 'Molecules',
        'content_heading': 'Molecules',
        'search_footer': True,
        'length_change': True,
        'ajax_url': reverse_lazy('molecule-all-ajax'),
        'initial_order': [Order(1, 'asc'), Order(2, 'asc')],
        'columns': [
            Column('Molecule', 'html', 0, True, True, True, ''),
            Column('<em>N</em><sub>atoms</sub>', 'number_atoms', 1, True, True, True, 'N'),
            Column('<em>m</em> (amu)', 'isotopologue__mass', 2, True, False, False, ''),
            Column('States', 'isotopologue__number_states', 3, True, False, False, ''),
            Column('Transitions', 'isotopologue__number_transitions', 4, True, False, False, ''),
        ]
    }


def molecule_details_html(molecule):
    return render_to_string('molecule_details.html', context={'molecule': molecule})


def number_states_value(molecule):
    val = molecule.isotopologue.number_states
    href = reverse('state-list', args=[molecule.slug])
    cls = 'elida-link'
    return f'<a href="{href}" class="{cls}">{val}</a>'


def number_transitions_value(molecule):
    val = molecule.isotopologue.number_transitions
    href = reverse('transition-list-mol_slug', args=[molecule.slug])
    cls = 'elida-link'
    return f'<a href="{href}" class="{cls}">{val}</a>'


class MoleculeDataTableAjaxView(ServerSideDataTableView):
    custom_value_getters = {
        'html': molecule_details_html,
        'isotopologue__mass': lambda mol: f'{mol.isotopologue.mass:.2f}',
        'isotopologue__number_states': number_states_value,
        'isotopologue__number_transitions': number_transitions_value
    }
    surrogate_columns_search = {'html': 'formula_str'}
    queryset = Molecule.objects.all()
