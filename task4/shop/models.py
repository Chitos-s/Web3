from django.db import models
from django.core.validators import MinValueValidator


class Customer(models.Model):
    name = models.CharField("имя", max_length=120)
    email = models.EmailField("email", unique=True)
    phone = models.CharField("телефон", max_length=30, blank=True)

    class Meta:
        verbose_name = "покупатель"
        verbose_name_plural = "покупатели"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField("название", max_length=120)
    price = models.DecimalField("цена", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.CharField("категория", max_length=80)

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Cart(models.Model):
    STATUS_CHOICES = [
        ("new", "Новая"),
        ("paid", "Оплачена"),
        ("sent", "Отправлена"),
        ("cancelled", "Отменена"),
    ]

    customer = models.ForeignKey(Customer, verbose_name="покупатель", on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through="CartItem", verbose_name="товары")
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    status = models.CharField("статус", max_length=20, choices=STATUS_CHOICES, default="new")

    class Meta:
        verbose_name = "корзина"
        verbose_name_plural = "корзины"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Корзина #{self.id} - {self.customer}"

    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    def total_price(self):
        return sum(item.quantity * item.product.price for item in self.items.all())

    def is_active(self):
        return self.status != "cancelled"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, verbose_name="корзина", related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="товар", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField("количество", default=1)

    class Meta:
        verbose_name = "товар в корзине"
        verbose_name_plural = "товары в корзине"

    def __str__(self):
        return f"{self.product} x {self.quantity}"

    def item_total(self):
        return self.quantity * self.product.price
