from django.views.generic import DetailView, ListView
from .models import State


class StateDetailView(DetailView):
    model = State
    template_name = 'state_detail.html'
    extra_context = {'title': 'State'}


class StateListView(ListView):
    template_name = 'state_list.html'
    extra_context = {'title': 'States'}

    def get_queryset(self):
        return State.objects.filter(isotopologue__molecule__slug=self.kwargs['mol_slug'])

