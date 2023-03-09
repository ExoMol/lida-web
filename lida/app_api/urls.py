from django.urls import path

from .views import ApiAboutView
from .views import api_endpoint

urlpatterns = [
    path("", api_endpoint, name="api_endpoint"),
    path("about/", ApiAboutView.as_view(), name="api-about")
]
