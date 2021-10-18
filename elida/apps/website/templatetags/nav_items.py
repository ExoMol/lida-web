from django import template

register = template.Library()


@register.simple_tag
def data_active(request):
    url_name = request.resolver_match.url_name
    for prefix in ['data', 'molecule', 'state', 'transition']:
        if url_name.startswith(prefix):
            return ' active'
    return ''


@register.simple_tag
def about_active(request):
    url_name = request.resolver_match.url_name
    if url_name in {'website-about', 'website-home'}:
        return ' active'
    return ''


@register.simple_tag
def api_active(request):
    url_name = request.resolver_match.url_name
    if url_name.startswith('api'):
        return ' active'
    return ''


@register.simple_tag
def contact_active(request):
    url_name = request.resolver_match.url_name
    if url_name == 'website-contact':
        return ' active'
    return ''
