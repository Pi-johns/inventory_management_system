from django.db import models
from sales.models import Sale
from inventory.models import Product
from django.utils.timezone import now
from django.contrib.auth import get_user_model


User = get_user_model()  # Dynamically gets the CustomUser model


class SalesReport(models.Model):
    """Stores summarized sales reports."""
    date = models.DateField(default=now)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sales Report - {self.date}"


class ProductPerformanceReport(models.Model):
    """Stores data about top and least selling products."""
    product_name = models.CharField(max_length=255)
    quantity_sold = models.PositiveIntegerField()
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_name} - {self.quantity_sold} units sold"

class AccountingReport(models.Model):
    """Stores accounting details including credit sales and profit analysis."""
    date = models.DateField(default=now)
    total_credit_sales = models.DecimalField(max_digits=12, decimal_places=2)
    total_cash_sales = models.DecimalField(max_digits=12, decimal_places=2)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2)
    balance_sheet = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Accounting Report - {self.date}"

class ProfitReport(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profit_reports")
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Profit Report ({self.seller.username} - {self.date})"