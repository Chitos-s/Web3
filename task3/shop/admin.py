from django.contrib import admin

from .models import Cart, Customer, Product


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone")
    search_fields = ("name", "email", "phone")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price")
    list_filter = ("category",)
    search_fields = ("name", "category")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "created_at", "product_count")
    list_filter = ("status", "created_at")
    search_fields = ("customer__name", "customer__email", "products__name")
    filter_horizontal = ("products",)

    @admin.display(description="товаров")
    def product_count(self, obj):
        return obj.product_count()
