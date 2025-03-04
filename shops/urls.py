from django.urls import path
from .views import (
     shop_list, create_shop,           
     edit_shop, delete_shop,
     get_shops,business_period_settings )

app_name = "shops"

urlpatterns = [
    #path("assign/", assign_seller, name="assign_seller"),
    path("list/", shop_list, name="shop_list"),
    path("create/", create_shop, name="create_shop"),
    path("<int:shop_id>/edit/", edit_shop, name="edit_shop"),
    path("<int:shop_id>/delete/", delete_shop, name="delete_shop"),
    path("settings/business-period/", business_period_settings, name="business_period_settings"),
    path("get-shops/", get_shops, name="get_shops"),  # New endpoint
]
