
from django.urls import path
from .views import StateDetailView, StateListView

urlpatterns = [
    path('<int:pk>/', StateDetailView.as_view(), name='state-detail-pk'),
    path('list/<str:mol_slug>/', StateListView.as_view(), name='state-list')
]
