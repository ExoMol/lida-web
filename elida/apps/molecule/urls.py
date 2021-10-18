from django.urls import path
from .views import MoleculeListView, MoleculeDetailView

urlpatterns = [
    path('all/', MoleculeListView.as_view(), name='molecule-all'),
    path('<str:slug>/', MoleculeDetailView.as_view(), name='molecule-detail-slug'),
]
