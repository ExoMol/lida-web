from django.shortcuts import render
from django.views.generic import DetailView, ListView
from .models import Transition
from elida.apps.state.models import State
from elida.apps.molecule.models import Molecule


class TransitionDetailView(DetailView):
    model = Transition
    template_name = 'transition_detail.html'
    extra_context = {'title': 'Transition'}


class TransitionListView(ListView):
    template_name = 'transition_list.html'
    paginate_by = 20

    header_appendix = ''

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        molecule = self.get_molecule()
        context_data['table_heading'] = f'Transitions of {molecule.html}' + self.header_appendix
        context_data['title'] = f'{molecule.slug} transitions'
        return context_data

    def get_state(self):
        return State.objects.get(pk=self.kwargs['state_pk'])

    def get_state_text(self):
        state_html = self.get_state().state_html
        if not state_html:
            state_text = 'ground state'
        else:
            state_text = f'state ({state_html})'
        return state_text

    def get_molecule(self):
        if 'mol_slug' in self.kwargs:
            return Molecule.objects.get(slug=self.kwargs['mol_slug'])
        elif 'state_pk' in self.kwargs:
            return self.get_state().isotopologue.molecule
        else:
            raise ValueError('If this happens, make sure that mol_slug or state_pk are passed to views from urls')


class TransitionToListView(TransitionListView):
    def get_queryset(self):
        return self.get_state().transition_to_set.all()

    @property
    def header_appendix(self):
        return f' to the {self.get_state_text()}'


class TransitionFromListView(TransitionListView):
    def get_queryset(self):
        return self.get_state().transition_from_set.all()

    @property
    def header_appendix(self):
        return f' from the {self.get_state_text()}'


class TransitionMoleculeListView(TransitionListView):
    def get_queryset(self):
        return self.get_molecule().isotopologue.transition_set.all()
