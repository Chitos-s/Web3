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
    products = models.ManyToManyField(Product, verbose_name="товары")
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    status = models.CharField("статус", max_length=20, choices=STATUS_CHOICES, default="new")

    class Meta:
        verbose_name = "корзина"
        verbose_name_plural = "корзины"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Корзина #{self.id} - {self.customer}"

    def product_count(self):
        return self.products.count()
