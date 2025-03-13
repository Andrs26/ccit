# miapp/templatetags/menu_tags.py
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def active(context, *url_names):
    """
    Retorna 'active' si el nombre de la URL actual está entre los especificados.
    """
    request = context.get('request')
    if not request:
        return ''
    # Obtiene el nombre de la URL actual
    current_url = request.resolver_match.url_name
    if current_url in url_names:
        return 'active'
    return ''
