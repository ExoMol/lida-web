from django.shortcuts import render
from django.views.generic import DetailView, ListView
from .models import Transition
from elida.apps.state.models import State


class TransitionDetailView(DetailView):
    model = Transition
    template_name = 'transition_detail.html'
    extra_context = {'title': 'Transition'}


class TransitionToListView(ListView):
    template_name = 'transition_list.html'
    extra_context = {'title': 'Transitions'}

    def get_queryset(self):
        return State.objects.get(pk=self.kwargs['state_pk']).transition_to_set.all()


class TransitionFromListView(ListView):
    template_name = 'transition_list.html'
    extra_context = {'title': 'Transitions'}

    def get_queryset(self):
        return State.objects.get(pk=self.kwargs['state_pk']).transition_from_set.all()
