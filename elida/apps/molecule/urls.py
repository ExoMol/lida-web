from django.urls import path
from .views import MoleculeListView

urlpatterns = [
    path('list/all/', MoleculeListView.as_view(), name='molecule-all'),
]
