from django.urls import path
from . import views

urlpatterns = [
    path('', views.about, name='blog-home'),
    path('about/', views.about, name='blog-about'),
]
