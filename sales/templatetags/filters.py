from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Fetch a dictionary item by key in Django templates"""
    return dictionary.get(key, 0)  # Return 0 if key does not exist
