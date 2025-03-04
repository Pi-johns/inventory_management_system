from django.urls import path
from .views import add_product, update_product, delete_product, product_list, low_stock_products_list, out_of_stock_products

app_name = "inventory"

urlpatterns = [
    path("add/", add_product, name="add_product"),
    path("update/<int:product_id>/", update_product, name="update_product"),
    path("delete/<int:product_id>/", delete_product, name="delete_product"),
    path("list/", product_list, name="product_list"),
    path("low-stock/", low_stock_products_list, name="low_stock_products_list"),
    path("out-of-stock/", out_of_stock_products, name="out_of_stock_products"),

]
