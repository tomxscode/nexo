from decimal import ROUND_HALF_UP, Decimal


def dec(value, places=2):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)