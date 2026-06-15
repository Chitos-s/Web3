from django.contrib import admin

from django.utils.html import format_html

from .models import Cart, CartItem, Customer, Product


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone")
    search_fields = ("name", "email", "phone")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price")
    list_filter = ("category",)
    search_fields = ("name", "category")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    min_num = 1


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status_badge", "created_at", "total_quantity", "total_price")
    list_filter = ("status", "created_at")
    search_fields = ("customer__name", "customer__email", "items__product__name")
    date_hierarchy = "created_at"
    inlines = [CartItemInline]
    readonly_fields = ("total_quantity", "total_price")
    fieldsets = (
        ("Основное", {"fields": ("customer", "status")}),
        ("Итоги корзины", {"fields": ("total_quantity", "total_price")}),
    )

    @admin.display(description="статус")
    def status_badge(self, obj):
        color = "#146c43" if obj.is_active() else "#b42318"
        bg = "#e6f4ea" if obj.is_active() else "#fdecec"
        return format_html(
            '<span style="padding:3px 8px;border-radius:12px;background:{};color:{};font-weight:700;">{}</span>',
            bg,
            color,
            obj.get_status_display(),
        )

    @admin.display(description="единиц товара")
    def total_quantity(self, obj):
        return obj.total_quantity()

    @admin.display(description="итоговая стоимость")
    def total_price(self, obj):
        return f"{obj.total_price()} руб."
