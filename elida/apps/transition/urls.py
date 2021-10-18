from django.urls import path
from .views import TransitionDetailView, TransitionToListView, TransitionFromListView

urlpatterns = [
    path('list/from_state/<int:state_pk>/', TransitionFromListView.as_view(), name='transition-list-from-state'),
    path('list/to_state/<int:state_pk>/', TransitionToListView.as_view(), name='transition-list-to-state'),
    path('<int:pk>/', TransitionDetailView.as_view(), name='transition-detail-pk'),
]
