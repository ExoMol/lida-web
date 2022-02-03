from django.urls import path

from ..views import (
    MoleculeListAjaxView,
    StateListAjaxView,
    TransitionListAjaxView,
    TransitionToStateListAjaxView,
    TransitionFromStateListAjaxView,
)

urlpatterns = [
    path(
        "molecule/list/all/", MoleculeListAjaxView.as_view(), name="molecule-list-ajax"
    ),
    path(
        "state/list/<str:mol_slug>", StateListAjaxView.as_view(), name="state-list-ajax"
    ),
    path(
        "transition/list/to_state/<int:state_pk>/",
        TransitionToStateListAjaxView.as_view(),
        name="transition-to-state-list-ajax",
    ),
    path(
        "transition/list/from_state/<int:state_pk>/",
        TransitionFromStateListAjaxView.as_view(),
        name="transition-from-state-list-ajax",
    ),
    path(
        "transition/list/<str:mol_slug>/",
        TransitionListAjaxView.as_view(),
        name="transition-list-ajax",
    ),
]
