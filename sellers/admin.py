from django.contrib import admin
from .models import Seller

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ("user", "shop", "phone", "created_at")
    search_fields = ("user__username", "shop__name", "phone")

