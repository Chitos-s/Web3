from django.db import models
from django.core.validators import MinValueValidator



class Book(models.Model):
    title = models.CharField("название", max_length=160)
    author = models.CharField("автор", max_length=120)
    genre = models.CharField("жанр", max_length=80)
    publication_date = models.DateField("дата публикации")
    pages = models.PositiveIntegerField("страниц")
    price = models.DecimalField("цена", max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    in_stock = models.BooleanField("в наличии", default=True)

    class Meta:
        verbose_name = "книга"
        verbose_name_plural = "книги"
        ordering = ["title"]

    def __str__(self):
        return self.title
