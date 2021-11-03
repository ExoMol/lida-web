
from django.urls import path
from .views import StateListView

urlpatterns = [
    path('list/<str:mol_slug>/', StateListView.as_view(), name='state-list'),
]
