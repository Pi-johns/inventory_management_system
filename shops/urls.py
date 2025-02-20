from django.urls import path
from .views import  shop_list, create_shop, edit_shop, delete_shop

app_name = "shops"

urlpatterns = [
    #path("assign/", assign_seller, name="assign_seller"),
    path("list/", shop_list, name="shop_list"),
    path("create/", create_shop, name="create_shop"),
    path("<int:shop_id>/edit/", edit_shop, name="edit_shop"),
    path("<int:shop_id>/delete/", delete_shop, name="delete_shop"),
]
