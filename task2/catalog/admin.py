from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "genre", "price", "in_stock")
    list_filter = ("genre", "in_stock")
    search_fields = ("title", "author")
