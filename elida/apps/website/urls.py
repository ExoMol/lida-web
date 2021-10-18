from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='website-home'),

    path('about/', views.about, name='website-about'),

    path('data/molecule/', include('elida.apps.molecule.urls')),
    path('data/state/', include('elida.apps.state.urls')),
    path('data/transition/', include('elida.apps.transition.urls')),

    path('contact/', views.contact, name='website-contact'),
]
