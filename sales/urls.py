from django.urls import path
from .views import (
    sales_list, sale_detail, record_sale,
      recordcredit_sale, sales_dashboard, sale_print, sale_pdf, sale_csv
)
app_name = 'sales'

urlpatterns = [
    path('', sales_dashboard, name='sales_dashboard'),
    path('sales/', sales_list, name='sales_list'),
    path('sales/<int:sale_id>/', sale_detail, name='sale_detail'),
    path('sales/<int:sale_id>/edit/', sale_detail, name='sale_edit'),
    path('sales/<int:sale_id>/delete/', sale_detail, name='sale_delete'),
    path('sales/<int:sale_id>/print/', sale_print, name='sale_print'),
    path('sales/<int:sale_id>/pdf/', sale_pdf, name='sale_pdf'),
    path('sales/<int:sale_id>/csv/', sale_csv, name='sale_csv'), 
    path('record/', record_sale, name='record_sale'),
    path('recordcredit/', recordcredit_sale, name='recordcredit_sale'),
    
]
