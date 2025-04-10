from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_dia(dias_qs, dia_codigo):
    try:
        return dias_qs.get(dia=dia_codigo)
    except:
        return None
    
@register.filter
def nombre_dia(codigo):
    nombres = {
        '0': 'Lunes',
        '1': 'Martes',
        '2': 'Miércoles',
        '3': 'Jueves',
        '4': 'Viernes',
        '5': 'Sábado',
        '6': 'Domingo',
    }
    return nombres.get(str(codigo), codigo)
