from django import template

register = template.Library()


@register.simple_tag
def data_active(request):
    url_name = request.resolver_match.url_name
    for prefix in ["molecule", "state", "transition"]:
        if url_name.startswith(prefix):
            return " active"
    return ""


@register.simple_tag
def about_active(request):
    url_name = request.resolver_match.url_name
    if url_name in {"site-about", "site-home"}:
        return " active"
    return ""


@register.simple_tag
def api_active(request):
    url_name = request.resolver_match.url_name
    if url_name.startswith("api"):
        return " active"
    return ""


@register.simple_tag
def contact_active(request):
    url_name = request.resolver_match.url_name
    if url_name == "site-contact":
        return " active"
    return ""
