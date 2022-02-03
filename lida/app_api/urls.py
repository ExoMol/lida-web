from django.urls import path

from .views import ApiAboutView

urlpatterns = [path("about/", ApiAboutView.as_view(), name="api-about")]
