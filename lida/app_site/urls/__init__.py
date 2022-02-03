from django.urls import path, include

from ..views import SiteAboutView, SiteContactView

urlpatterns = [
    path("", SiteAboutView.as_view(), name="site-home"),
    path("about/", SiteAboutView.as_view(), name="site-about"),
    path("contact/", SiteContactView.as_view(), name="site-contact"),
    path("", include("app_site.urls.urls_html")),
    path("ajax/", include("app_site.urls.urls_ajax")),
]
