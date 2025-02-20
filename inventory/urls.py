from django.urls import path
from .views import add_product, update_product, delete_product, product_list

app_name = "inventory"

urlpatterns = [
    path("add/", add_product, name="add_product"),
    path("update/<int:product_id>/", update_product, name="update_product"),
    path("delete/<int:product_id>/", delete_product, name="delete_product"),
    path("list/", product_list, name="product_list"),
]
