from django.urls import path
from . import views


urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    path('sales/', views.sales_report, name='sales_report'),
    path('expenses/', views.expense_report, name='expense_report'),
    path('damages/', views.damage_report, name='damage_report'),
    path('top-products/', views.top_products_report, name='top_products_report'),
    path('net-profit/', views.net_profit_report, name='net_profit_report'),

    # Export CSV URLs
    path('export/sales/', views.export_sales_csv, name='export_sales_csv'),
    path('export/expenses/', views.export_expenses_csv, name='export_expenses_csv'),
   # path('export/damages/', views.export_damages_csv, name='export_damages_csv'),
]
