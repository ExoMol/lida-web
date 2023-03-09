from django.views.generic import TemplateView


class SiteAboutView(TemplateView):
    template_name = "site/about.html"
    extra_context = {"title": "About", "content_heading": "About LiDB"}


class SiteContactView(TemplateView):
    template_name = "site/contact.html"
    extra_context = {"title": "Contact", "content_heading": "Contact"}
