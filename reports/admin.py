from django.contrib import admin
from .models import SalesReport, ProductPerformanceReport, AccountingReport, ProfitReport

# Register your models here.
admin.site.register(SalesReport)
admin.site.register(ProductPerformanceReport)
admin.site.register(AccountingReport)
admin.site.register(ProfitReport)