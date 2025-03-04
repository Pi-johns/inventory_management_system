from django.urls import path
from .views import (
    sales_list, 
    delete_sale, 
    mark_sale_as_paid,
    credit_sales_view, 
    manager_record_sale,
    return_sale_as_damaged,
    return_sale_to_stock,
    mark_item_as_damaged,
    mark_item_as_returned_to_stock,
    damaged_goods_list,
    export_damaged_goods_csv,
    export_damaged_goods_pdf, mark_stock_as_damaged
    
)

app_name = 'sales'

urlpatterns = [
    path('sales/', sales_list, name='sales_list'),
    path('record/manager/', manager_record_sale, name='manager_record_sale'),

    # Sales Actions
    path("sales/mark/<int:sale_id>/", mark_sale_as_paid, name="mark_sale_as_paid"),
    path("sales/delete/<int:sale_id>/", delete_sale, name="delete_sale"),
    path("credit-sales/", credit_sales_view, name="credit_sales"),
    
    # Damaged Goods List & Export
    path('damaged-goods/', damaged_goods_list, name='damaged_goods_list'),
    path('damaged-goods/export/csv/', export_damaged_goods_csv, name='export_damaged_goods_csv'),
    path('damaged-goods/export/pdf/', export_damaged_goods_pdf, name='export_damaged_goods_pdf'),
    
    # Sales Return Actions
    path("sales/return/damaged/<int:sale_id>/", return_sale_as_damaged, name="return_sale_as_damaged"),
    path("sales/return/stock/<int:sale_id>/", return_sale_to_stock, name="return_sale_to_stock"),
    
    # Item-Level Returns
    path("mark-damaged/", mark_stock_as_damaged, name="mark_stock_as_damaged"),

    path("sales/item/damaged/<int:item_id>/", mark_item_as_damaged, name="mark_item_damaged"),
    path("sales/item/return/<int:item_id>/", mark_item_as_returned_to_stock, name="mark_item_returned_to_stock"),
]
