from django.urls import path

from .views import MoleculeListView, MoleculeDataTableAjaxView

urlpatterns = [
    path('list/all/', MoleculeListView.as_view(), name='molecule-all'),
    path('ajax/list/all/', MoleculeDataTableAjaxView.as_view(), name='molecule-all-ajax')
]
