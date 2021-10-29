from django.urls import path
from .views import TransitionToListView, TransitionFromListView, TransitionMoleculeListView

urlpatterns = [
    path('list/from_state/<int:state_pk>/', TransitionFromListView.as_view(), name='transition-list-from-state'),
    path('list/to_state/<int:state_pk>/', TransitionToListView.as_view(), name='transition-list-to-state'),
    path('list/<str:mol_slug>/', TransitionMoleculeListView.as_view(), name='transition-list-mol_slug'),
]
