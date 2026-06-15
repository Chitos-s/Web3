from decimal import Decimal

from django import template

register = template.Library()


@register.simple_tag
def catalog_title(total):
    return f"Каталог книг: {total}"


@register.simple_tag
def availability_label(book):
    return "В наличии" if book.in_stock else "Нет в наличии"


@register.simple_tag
def reading_time(pages, pages_per_hour=35):
    hours = int(pages) / pages_per_hour
    return f"{hours:.1f} ч."


@register.filter
def rubles(value):
    amount = Decimal(value)
    return f"{amount:,.2f} руб.".replace(",", " ")


@register.filter
def initials(name):
    parts = str(name).split()
    if len(parts) < 2:
        return name
    return f"{parts[-1]} {parts[0][0]}."


@register.filter
def badge(value):
    return f"[{value}]"
