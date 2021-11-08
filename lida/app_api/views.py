from django.views.generic import TemplateView


class ApiAboutView(TemplateView):
    template_name = 'api/about.html'
    extra_context = {'title': 'API', 'content_heading': 'About the public API'}
