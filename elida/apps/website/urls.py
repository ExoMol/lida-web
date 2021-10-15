from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='website-home'),
    path('about/', views.about, name='website-about'),
    path('data/', views.data, name='website-data'),
    path('contact/', views.contact, name='website-contact'),
]
