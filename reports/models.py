from django.db import models
from django.conf import settings  # Import settings
from django.contrib.auth.models import User
from inventory.models import Product
from shops.models import Shop  # Assuming you have a Shop model

class SalesReport(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Fix here
    date = models.DateField()
    total_sales_count = models.PositiveIntegerField(default=0)
    total_sales_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_credit_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_partial_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Sales Report ({self.date}) - Shop: {self.shop or 'All'}"

class ProfitReport(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Fix here
    date = models.DateField()
    total_cash_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_partial_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_credit_unrealized_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Profit Report ({self.date}) - Shop: {self.shop or 'All'}"

class ExpenseReport(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    num_expenses = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Expense Report ({self.date}) - Shop: {self.shop or 'All'}"

class DamageReport(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    total_damaged_count = models.PositiveIntegerField(default=0)
    total_loss_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Damage Report ({self.date}) - Shop: {self.shop or 'All'}"

class TopProductsReport(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_sold = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.product.name} - {self.quantity_sold} sold ({self.date})"
