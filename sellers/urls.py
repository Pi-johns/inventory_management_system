from django.urls import path
from .views import edit_sale, seller_dashboard, seller_create_sale, seller_list, create_seller, edit_seller, delete_seller, make_payment

app_name = "sellers"

urlpatterns = [
    path("", seller_list, name="seller_list"),
    path("create/", create_seller, name="create_seller"),
    path("edit/<int:seller_id>/", edit_seller, name="edit_seller"),
    path('dashboard/', seller_dashboard, name='seller_dashboard'),
    path("delete/<int:seller_id>/", delete_seller, name="delete_seller"),
    path("credit-sales/pay/<int:sale_id>/", make_payment, name="make_payment"),
    path('seller/create', seller_create_sale, name='seller_create_sale'),
    path("sales/edit/<int:sale_id>/", edit_sale, name="edit_sale"),


]

