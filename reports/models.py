from django.db import models
from shops.models import Shop
from inventory.models import Product
from django.utils.timezone import now
from django.contrib.auth import get_user_model


User = get_user_model()  # ✅ Dynamically fetches the CustomUser model

### ✅ SalesReport - Tracks daily total sales & profit ###
class SalesReport(models.Model):
    """Stores summarized sales reports for a specific date and shop."""
    date = models.DateField(default=now)  # ✅ No `unique=True`, allows multiple reports for different shops
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True)  # ✅ Track per shop
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Sum of sales
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Profit calculation
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("date", "shop")  # ✅ Ensures one report per shop per day

    def __str__(self):
        return f"Sales Report - {self.date} ({self.shop.name if self.shop else 'All Shops'})"

### ✅ Product Performance Report - Tracks best & worst selling products ###
class ProductPerformanceReport(models.Model):
    """Tracks top and least selling products per shop and date."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="performance_reports")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True)  # ✅ Track per shop
    date = models.DateField(default=now)  # ✅ Track per day
    quantity_sold = models.PositiveIntegerField(default=0)  # ✅ Total quantity sold
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Revenue from product
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("date", "product", "shop")  # ✅ Unique per product per shop per day

    def __str__(self):
        return f"{self.product.name} - {self.quantity_sold} units sold ({self.date})"

### ✅ Accounting Report - Tracks Credit Sales & Profits ###
class AccountingReport(models.Model):
    """Tracks total credit & cash sales, profit, and balance sheet per shop."""
    date = models.DateField(default=now)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True)  # ✅ Track per shop
    total_credit_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Sum of credit sales
    total_cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Sum of cash sales
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Profit calculation
    balance_sheet = models.TextField(blank=True, null=True)  # ✅ Allows empty balance sheet notes
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("date", "shop")  # ✅ Ensures one report per shop per day

    def __str__(self):
        return f"Accounting Report - {self.date} ({self.shop.name if self.shop else 'All Shops'})"

### ✅ Profit Report - Tracks Profit per Seller ###
class ProfitReport(models.Model):
    """Tracks revenue, cost, and net profit per seller."""
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name="profit_reports")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True)  # ✅ Track per shop
    date = models.DateField(default=now)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Total earnings from sales
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Cost of sold products
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Total profit calculation
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("date", "seller", "shop")  # ✅ Ensures one report per seller per shop per day

    def __str__(self):
        return f"Profit Report ({self.seller.username} - {self.date})"


class BalanceSheet(models.Model):
    date = models.DateField(auto_now_add=True)  # ✅ Auto-assign today's date
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, null=True, blank=True)  # ✅ Track balances per shop
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Total sales recorded
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Total payments received
    total_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # ✅ Remaining credit balance

    class Meta:
        unique_together = ("date", "shop")  # ✅ Ensures one balance sheet per shop per day

    def save(self, *args, **kwargs):
        """Automatically update total_credit before saving."""
        self.total_credit = self.total_sales - self.total_paid  # ✅ Auto-calculate outstanding credit
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Balance Sheet ({self.date}) - {self.shop.name if self.shop else 'All Shops'}"