
from django.urls import path
from .views import StateListView

urlpatterns = [
    path('list/<str:mol_slug>/', StateListView.as_view(), name='state-list'),
    path('list-new/<str:mol_slug>/', StateListView.as_view(template_name='state_list_new.html'), name='state-list-new')
]
