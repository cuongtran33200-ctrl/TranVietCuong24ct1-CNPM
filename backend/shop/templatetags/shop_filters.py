from django import template

register = template.Library()


@register.filter(name='vnd')
def format_vnd(value):
    """
    Format a number with dot separators for Vietnamese currency.
    Example: 3690000 → 3.690.000
    Usage: {{ product.price|vnd }}đ  or  {{ product.price|vnd }}₫
    """
    try:
        value = int(float(value))
        return "{:,}".format(value).replace(",", ".")
    except (ValueError, TypeError):
        return value
