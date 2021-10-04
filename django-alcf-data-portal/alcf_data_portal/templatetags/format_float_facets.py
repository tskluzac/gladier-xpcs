from django import template
from django.template.defaultfilters import stringfilter, floatformat

register = template.Library()

SEPARATOR = '--'


@register.filter
@stringfilter
def format_float_facets(value, arg='2'):
    if not value or SEPARATOR not in value:
        return value
    try:
        val1, val2 = value.split(SEPARATOR)
        # Sometimes Globus Search returns floats as '*' for open ended ranges
        # Run both non * floats through float format.
        vals = [floatformat(float(val), arg) if val != '*' else val
                for val in (val1, val2)]
        return SEPARATOR.join(vals)
    except Exception as e:
        print(e)
    return value
