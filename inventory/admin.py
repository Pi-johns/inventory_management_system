from django.contrib import admin
from .models import Product, StockLog

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "entry_price", "stock_quantity", "low_stock_threshold", "created_at")
    search_fields = ("name",)

@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ("product", "change", "description", "timestamp")
    search_fields = ("product__name",)
