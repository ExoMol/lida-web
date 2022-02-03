from django.urls import path

from ..views import (
    MoleculeListView,
    StateListView,
    TransitionToStateListView,
    TransitionFromStateListView,
    TransitionListView,
)

urlpatterns = [
    path("molecule/list/all/", MoleculeListView.as_view(), name="molecule-list"),
    path("state/list/<str:mol_slug>", StateListView.as_view(), name="state-list"),
    path(
        "transition/list/to_state/<int:state_pk>/",
        TransitionToStateListView.as_view(),
        name="transition-to-state-list",
    ),
    path(
        "transition/list/from_state/<int:state_pk>/",
        TransitionFromStateListView.as_view(),
        name="transition-from-state-list",
    ),
    path(
        "transition/list/<str:mol_slug>/",
        TransitionListView.as_view(),
        name="transition-list",
    ),
]
