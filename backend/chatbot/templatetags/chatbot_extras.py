from django import template
import json

register = template.Library()


@register.filter
def pprint(value):
    """Pretty print JSON data"""
    try:
        return json.dumps(value, indent=2, sort_keys=True)
    except (TypeError, ValueError):
        return value
