# compras/templatetags/compras_extras.py
from django import template

register = template.Library()

@register.filter
def sum_attribute(queryset, attr):
    return sum(getattr(obj, attr)() if callable(getattr(obj, attr, None)) else getattr(obj, attr, 0) for obj in queryset)

