from django.urls import path
from .views import (
sales_report_view,
product_performance_view,
accounting_report_view,
profit_analysis,
reports_data,
reports_dashboard,
export_sales_csv,
export_sales_pdf,
export_balance_csv,
export_balance_pdf,
)

app_name = "reports"

urlpatterns = [
# Main reports pages
path('sales/', sales_report_view, name='sales_report'),
path('products/', product_performance_view, name='product_performance'),
path('accounting/', accounting_report_view, name='accounting_report'),
path("profit-analysis/", profit_analysis, name="profit_analysis"),

# Data API for dynamic Chart.js integration
path("data/", reports_data, name="reports_data"),

# Full dashboard views for reports
path("dashboard/", reports_dashboard, name="reports_dashboard"),


# Export endpoints for Sales Reports
path("export/sales/csv/", export_sales_csv, name="export_sales_csv"),
path("export/sales/pdf/", export_sales_pdf, name="export_sales_pdf"),
# Export endpoints for Balance Sheet/Accounting Reports
path("export/balance/csv/", export_balance_csv, name="export_balance_csv"),
path("export/balance/pdf/", export_balance_pdf, name="export_balance_pdf"),
]


