from django.urls import path

from .views import BookListView

app_name = "catalog"

urlpatterns = [
    path("", BookListView.as_view(), name="book_list"),
]
