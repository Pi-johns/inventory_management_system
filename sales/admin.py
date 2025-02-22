from django.contrib import admin
from .models import Sale, SaleItem

### ✅ INLINE ADMIN FOR SALE ITEMS ###
class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    readonly_fields = ("product", "quantity", "price_per_piece", "total_price")  # ✅ Fixed

    def total_price(self, obj):
        return obj.total_price()

    total_price.short_description = "Total Price"


### ✅ ADMIN FOR SALE ###
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("id", "seller", "total_amount", "amount_paid", "balance", "payment_status", "date")
    list_filter = ("payment_status", "date")
    search_fields = ("seller__username", "customer_name")
    inlines = [SaleItemInline]


### ✅ ADMIN FOR SALE ITEM ###
@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "price_per_piece", "total_price")

    def total_price(self, obj):
        return obj.total_price()
