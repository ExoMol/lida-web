from django.urls import path
from . import views

urlpatterns = [
    path('', views.about, name='website-home'),
    path('about/', views.about, name='website-about'),
]
