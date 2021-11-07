from django.urls import path

from .views import (TransitionToListView, TransitionFromListView, TransitionMoleculeListView,
                    TransitionToDataTableAjaxView, TransitionFromDataTableAjaxView, TransitionMoleculeDataTableAjaxView)

urlpatterns = [
    path('list/from_state/<int:state_pk>/', TransitionFromListView.as_view(), name='transition-list-from-state'),
    path('list/to_state/<int:state_pk>/', TransitionToListView.as_view(), name='transition-list-to-state'),
    path('list/<str:mol_slug>/', TransitionMoleculeListView.as_view(), name='transition-list-mol_slug'),

    path('ajax/list/from_state/<int:state_pk>/', TransitionFromDataTableAjaxView.as_view(),
         name='transition-list-from-state-ajax'),
    path('ajax/list/to_state/<int:state_pk>/', TransitionToDataTableAjaxView.as_view(),
         name='transition-list-to-state-ajax'),
    path('ajax/list/<str:mol_slug>/', TransitionMoleculeDataTableAjaxView.as_view(),
         name='transition-list-mol_slug-ajax'),
]
