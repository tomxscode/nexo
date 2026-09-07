from pathlib import Path

from django import template

register = template.Library()


@register.filter
def clp(value):
    """Formatea un monto como pesos chilenos: $1.234.567 (sin decimales)."""
    try:
        amount = int(round(float(value)))
    except (TypeError, ValueError):
        return "$0"
    negative = amount < 0
    digits = f"{abs(amount):,}".replace(",", ".")
    return f"${'-' if negative else ''}{digits}"