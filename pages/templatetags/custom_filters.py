from django import template
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))

@register.filter
def split(value, delimiter):
    return value.split(delimiter)

@register.filter
def startswith(text, prefix):
    return text.startswith(prefix)

@register.filter(name="strip")
def strip(value):
    return value.strip()

@register.filter
def contains(value, substring):
    return substring in value