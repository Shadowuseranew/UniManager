from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    return d.get(key)

@register.simple_tag(takes_context=True)
def url_replace(context, param, value):
    request = context['request']
    params = request.GET.copy()
    params[param] = value
    return params.urlencode()
