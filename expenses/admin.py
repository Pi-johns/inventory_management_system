from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "category", "recorded_by", "date_recorded")
    search_fields = ("description", "category")
    list_filter = ("category", "date_recorded")

