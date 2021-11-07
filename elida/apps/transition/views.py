from collections import namedtuple

from django.urls import reverse
from django.views.generic import TemplateView
from django_datatables_serverside.views import ServerSideDataTableView

from elida.apps.molecule.models import Molecule
from elida.apps.state.models import State

# TODO: the same classes are defined also in molecule and state! Clean up!
Column = namedtuple('Column', 'heading model_field index visible searchable individual_search')
Order = namedtuple('Order', 'index dir')


class Base(TemplateView):
    template_name = 'datatable.html'
    extra_context = {
        'search_footer': True, 'length_change': True, 'initial_order': [Order(0, 'asc'), Order(1, 'asc')],
        'columns': [
            Column('Initial state', 'initial_state__state_html', 0, True, True, True),
            Column('Final state', 'final_state__state_html', 1, True, True, True),
            Column('Δ<em>E</em> (eV)', 'delta_energy', 2, True, False, False),
            Column('Partial lifetime (s)', 'partial_lifetime', 3, True, False, False),
            Column('Branching ratio', 'branching_ratio', 4, True, False, False),
        ]
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state, self.molecule = None, None

    def get_context_data(self, **kwargs):
        self.save_state_and_molecule()
        context = super().get_context_data(**kwargs)
        context['title'] = f'{self.molecule.slug} transitions'
        context['search_footer'] = True
        context['length_change'] = True
        # to be implemented in the child classes:
        context['content_heading'] = None
        context['ajax_url'] = None
        return context

    def save_state_and_molecule(self):
        if 'mol_slug' in self.kwargs:
            self.state = None
            self.molecule = Molecule.objects.get(slug=self.kwargs['mol_slug'])
        elif 'state_pk' in self.kwargs:
            self.state = State.objects.get(pk=self.kwargs['state_pk'])
            self.molecule = self.state.isotopologue.molecule
        else:
            raise ValueError('If this happens, make sure that mol_slug or state_pk are passed to views from urls')


class TransitionToListView(Base):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_heading'] = f'Transitions of {self.molecule.html} to the state {self.state.state_html}'
        context['ajax_url'] = reverse('transition-list-to-state-ajax', args=[self.state.pk])
        return context


class TransitionFromListView(Base):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_heading'] = f'Transitions of {self.molecule.html} from the state {self.state.state_html}'
        context['ajax_url'] = reverse('transition-list-from-state-ajax', args=[self.state.pk])
        return context


class TransitionMoleculeListView(Base):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_heading'] = f'Transitions of {self.molecule.html}'
        context['ajax_url'] = reverse('transition-list-mol_slug-ajax', args=[self.molecule.slug])
        return context


class BaseAjax(ServerSideDataTableView):
    surrogate_columns_search = {'initial_state__state_html': 'initial_state__state_html_notags',
                                'final_state__state_html': 'final_state__state_html_notags'}
    surrogate_columns_sort = {'initial_state__state_html': 'initial_state__state_sort_key',
                              'final_state__state_html': 'final_state__state_sort_key'}
    custom_value_getters = {
        'delta_energy': lambda tr: f'{tr.delta_energy:.3f}',
        'partial_lifetime': lambda tr: f'{tr.partial_lifetime:.2e}' if tr.partial_lifetime is not None else '∞',
        'branching_ratio': lambda tr: f'{tr.branching_ratio:.2e}'
    }
    queryset = None


class TransitionToDataTableAjaxView(BaseAjax):
    @property
    def queryset(self):
        return State.objects.get(pk=self.kwargs['state_pk']).transition_to_set.all()


class TransitionFromDataTableAjaxView(BaseAjax):
    @property
    def queryset(self):
        return State.objects.get(pk=self.kwargs['state_pk']).transition_from_set.all()


class TransitionMoleculeDataTableAjaxView(BaseAjax):
    @property
    def queryset(self):
        return Molecule.objects.get(slug=self.kwargs['mol_slug']).isotopologue.transition_set.all()
