from django.views.generic import ListView
from elida.apps.state.models import State
from elida.apps.molecule.models import Molecule


class TransitionListView(ListView):
    template_name = 'transition_list.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        molecule = self.get_molecule()
        context_data['content_heading'] = f'Transitions' + self.header_appendix
        context_data['title'] = f'{molecule.slug} transitions'
        return context_data

    def get_state(self):
        return State.objects.get(pk=self.kwargs['state_pk'])

    def get_molecule(self):
        if 'mol_slug' in self.kwargs:
            return Molecule.objects.get(slug=self.kwargs['mol_slug'])
        elif 'state_pk' in self.kwargs:
            return self.get_state().isotopologue.molecule
        else:
            raise ValueError('If this happens, make sure that mol_slug or state_pk are passed to views from urls')

    @property
    def header_appendix(self):
        return f' of {self.get_molecule().html}'


class TransitionToListView(TransitionListView):
    def get_queryset(self):
        return self.get_state().transition_to_set.all()

    @property
    def header_appendix(self):
        return f' to the state {self.get_state().html}'


class TransitionFromListView(TransitionListView):
    def get_queryset(self):
        return self.get_state().transition_from_set.all()

    @property
    def header_appendix(self):
        return f' from the state {self.get_state().html}'


class TransitionMoleculeListView(TransitionListView):
    def get_queryset(self):
        return self.get_molecule().isotopologue.transition_set.all()
