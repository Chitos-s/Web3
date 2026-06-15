from decimal import Decimal

from django.db import migrations, models

from django.core.validators import MinValueValidator



def add_books(apps, schema_editor):
    Book = apps.get_model("catalog", "Book")
    Book.objects.bulk_create(
        [
            Book(
                title="Война и мир",
                author="Лев Толстой",
                genre="Классика",
                publication_date="1869-01-01",
                pages=1225,
                price=Decimal("950.00"),
                in_stock=True,
            ),
            Book(
                title="Гарри Поттер",
                author="Джоан Роулинг",
                genre="Фэнтези",
                publication_date="1997-06-26",
                pages=432,
                price=Decimal("640.50"),
                in_stock=True,
            ),
            Book(
                title="Чистый код",
                author="Роберт Мартин",
                genre="Программирование",
                publication_date="2008-08-01",
                pages=464,
                price=Decimal("1800.00"),
                in_stock=False,
            ),
            Book(
                title="Краткая история времени",
                author="Стивен Хокинг",
                genre="Научпоп",
                publication_date="1988-04-01",
                pages=256,
                price=Decimal("720.00"),
                in_stock=True,
            ),
        ]
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Book",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160, verbose_name="название")),
                ("author", models.CharField(max_length=120, verbose_name="автор")),
                ("genre", models.CharField(max_length=80, verbose_name="жанр")),
                ("publication_date", models.DateField(verbose_name="дата публикации")),
                ("pages", models.PositiveIntegerField(verbose_name="страниц")),
                ("price", models.DecimalField(decimal_places=2, max_digits=8, verbose_name="цена", validators=[MinValueValidator(0)])),
                ("in_stock", models.BooleanField(default=True, verbose_name="в наличии")),
            ],
            options={
                "verbose_name": "книга",
                "verbose_name_plural": "книги",
                "ordering": ["title"],
            },
        ),
        migrations.RunPython(add_books),
    ]
