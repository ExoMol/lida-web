from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .utils import Column, Order


class MoleculeListView(TemplateView):
    template_name = 'datatable.html'
    extra_context = {
        'title': 'Molecules',
        'content_heading': 'Molecules',
        'search_footer': True,
        'length_change': True,
        'ajax_url': reverse_lazy('molecule-list-ajax'),
        'initial_order': [Order(1, 'asc'), Order(2, 'asc')],
        'columns': [
            Column('Molecule', 'html', 0, True, True, True, ''),
            Column('<em>N</em><sub>atoms</sub>', 'number_atoms', 1, True, True, True, 'N'),
            Column('<em>m</em> (amu)', 'isotopologue__mass', 2, True, False, False, ''),
            Column('States', 'isotopologue__number_states', 3, True, False, False, ''),
            Column('Transitions', 'isotopologue__number_transitions', 4, True, False, False, ''),
        ]
    }
