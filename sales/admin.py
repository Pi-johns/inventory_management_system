from django.contrib import admin
from .models import Sale, SaleItem, CreditSale

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'shop', 'date', 'total_amount', 'is_credit', 'is_paid')
    search_fields = ('seller__username', 'shop__name', 'customer_name')
    list_filter = ('shop', 'is_credit', 'is_paid', 'date')
    inlines = [SaleItemInline]

@admin.register(CreditSale)
class CreditSaleAdmin(admin.ModelAdmin):
    list_display = ('sale', 'paid', 'paid_date')
    list_filter = ('paid',)
