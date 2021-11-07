
from django.urls import path
from .views import StateListView, StateDataTableAjaxView

urlpatterns = [
    path('list/<str:mol_slug>/', StateListView.as_view(), name='state-list'),
    path('ajax/list/<str:mol_slug>', StateDataTableAjaxView.as_view(), name='state-list-ajax')
]
