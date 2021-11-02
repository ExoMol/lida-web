from django.urls import path
from .views import StateListAjaxView
# from .views import TransitionFromListAjaxView, TransitionToListAjaxView, TransitionMoleculeListAjaxView

urlpatterns = [
    path('state/list/<str:mol_slug>/', StateListAjaxView.as_view(), name='state-list-ajax'),
    # path('transition/list/from_state/<int:state_pk>/', TransitionFromListAjaxView.as_view(),
    #      name='transition-list-from-state-ajax'),
    # path('transition/list/to_state/<int:state_pk>/', TransitionToListAjaxView.as_view(),
    #      name='transition-list-to-state-ajax'),
    # path('transition/list/<str:mol_slug>/', TransitionMoleculeListAjaxView.as_view(),
    #      name='transition-list-mol_slug-ajax'),
]