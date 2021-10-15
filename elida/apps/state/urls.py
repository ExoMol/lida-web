
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dummy, name='api-dummy')
]
