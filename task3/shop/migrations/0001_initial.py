from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MinValueValidator


def add_demo_data(apps, schema_editor):
    Customer = apps.get_model("shop", "Customer")
    Product = apps.get_model("shop", "Product")
    Cart = apps.get_model("shop", "Cart")

    anna = Customer.objects.create(name="Анна Иванова", email="anna@example.com", phone="+7 900 111-22-33")
    oleg = Customer.objects.create(name="Олег Петров", email="oleg@example.com", phone="+7 900 444-55-66")

    keyboard = Product.objects.create(name="Клавиатура", category="Компьютеры", price=Decimal("3500.00"))
    mouse = Product.objects.create(name="Мышь", category="Компьютеры", price=Decimal("1200.00"))
    headphones = Product.objects.create(name="Наушники", category="Аудио", price=Decimal("4900.00"))
    book = Product.objects.create(name="Книга Django", category="Книги", price=Decimal("1500.00"))

    cart1 = Cart.objects.create(customer=anna, status="new")
    cart1.products.set([keyboard, mouse, book])

    cart2 = Cart.objects.create(customer=oleg, status="paid")
    cart2.products.set([headphones, mouse])


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="имя")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="email")),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="телефон")),
            ],
            options={
                "verbose_name": "покупатель",
                "verbose_name_plural": "покупатели",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="название")),
                ("price", models.DecimalField(decimal_places=2, max_digits=8, verbose_name="цена", validators=[MinValueValidator(0)])),
                ("category", models.CharField(max_length=80, verbose_name="категория")),
            ],
            options={
                "verbose_name": "товар",
                "verbose_name_plural": "товары",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Cart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="дата создания")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "Новая"),
                            ("paid", "Оплачена"),
                            ("sent", "Отправлена"),
                            ("cancelled", "Отменена"),
                        ],
                        default="new",
                        max_length=20,
                        verbose_name="статус",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="shop.customer",
                        verbose_name="покупатель",
                    ),
                ),
                ("products", models.ManyToManyField(to="shop.product", verbose_name="товары")),
            ],
            options={
                "verbose_name": "корзина",
                "verbose_name_plural": "корзины",
                "ordering": ["-created_at"],
            },
        ),
        migrations.RunPython(add_demo_data),
    ]
