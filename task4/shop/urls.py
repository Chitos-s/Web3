from django.urls import path

from .views import CartListView

urlpatterns = [
    path("carts/", CartListView.as_view(), name="cart_list"),
]
