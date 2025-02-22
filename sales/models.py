from django.db import models
from django.utils.timezone import now
from accounts.models import CustomUser  # Seller reference
from inventory.models import Product
from shops.models import Shop
from reports.models import SalesReport, AccountingReport, ProfitReport

class Sale(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("Paid", "Paid"),
        ("Partial", "Partial Payment"),
        ("Credit", "Credit"),
    ]

    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'seller'})
    product = models.ForeignKey(Product, on_delete=models.CASCADE, default=1)  
    quantity = models.PositiveIntegerField(default=1)  
    price_per_piece = models.DecimalField(max_digits=10, decimal_places=2)  
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)  
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default="Credit")  
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_phone = models.CharField(max_length=15, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Sale {self.id} - {self.product.name} ({self.payment_status})"

    def save(self, *args, **kwargs):
        """Automatically calculate total amount, balance, update payment status, and stock."""
        self.total_amount = self.quantity * self.price_per_piece  
        self.balance = self.total_amount - self.amount_paid  

        # ✅ Update payment status
        if self.amount_paid == 0:
            self.payment_status = "Credit"
        elif self.balance == 0:
            self.payment_status = "Paid"
        else:
            self.payment_status = "Partial"

        # ✅ Deduct stock only when the sale is first created
        if not self.pk:
            self.product.stock_quantity -= self.quantity
            self.product.save()

        super().save(*args, **kwargs)

        # ✅ Update Reports
        self.update_reports()

    def update_reports(self):
        """Update Sales Report, Accounting Report, and Profit Report"""
        # ✅ Update SalesReport
        sales_report, _ = SalesReport.objects.get_or_create(date=self.date.date(), shop=self.shop)
        sales_report.total_sales += self.total_amount
        sales_report.total_profit += (self.total_amount - (self.product.cost_price * self.quantity))
        sales_report.save()

        # ✅ Update AccountingReport
        accounting_report, _ = AccountingReport.objects.get_or_create(date=self.date.date(), shop=self.shop)
        if self.payment_status == "Credit":
            accounting_report.total_credit_sales += self.total_amount
        else:
            accounting_report.total_cash_sales += self.total_amount
        accounting_report.total_profit += (self.total_amount - (self.product.cost_price * self.quantity))
        accounting_report.save()

        # ✅ Update ProfitReport
        profit_report, _ = ProfitReport.objects.get_or_create(date=self.date.date(), seller=self.seller, shop=self.shop)
        profit_report.total_revenue += self.total_amount
        profit_report.total_cost += (self.product.cost_price * self.quantity)
        profit_report.net_profit = profit_report.total_revenue - profit_report.total_cost
        profit_report.save()

    def delete(self, *args, **kwargs):
        """Restore stock and update reports when a sale is deleted"""
        self.product.stock_quantity += self.quantity  # ✅ Restore stock
        self.product.save()

        # ✅ Update reports when sale is removed
        self.update_reports_on_delete()

        super().delete(*args, **kwargs)

    def update_reports_on_delete(self):
        """Adjust reports when a sale is deleted"""
        # ✅ Adjust Sales Report
        sales_report = SalesReport.objects.filter(date=self.date.date(), shop=self.shop).first()
        if sales_report:
            sales_report.total_sales -= self.total_amount
            sales_report.total_profit -= (self.total_amount - (self.product.cost_price * self.quantity))
            sales_report.save()

        # ✅ Adjust Accounting Report
        accounting_report = AccountingReport.objects.filter(date=self.date.date(), shop=self.shop).first()
        if accounting_report:
            if self.payment_status == "Credit":
                accounting_report.total_credit_sales -= self.total_amount
            else:
                accounting_report.total_cash_sales -= self.total_amount
            accounting_report.total_profit -= (self.total_amount - (self.product.cost_price * self.quantity))
            accounting_report.save()

        # ✅ Adjust Profit Report
        profit_report = ProfitReport.objects.filter(date=self.date.date(), seller=self.seller, shop=self.shop).first()
        if profit_report:
            profit_report.total_revenue -= self.total_amount
            profit_report.total_cost -= (self.product.cost_price * self.quantity)
            profit_report.net_profit = profit_report.total_revenue - profit_report.total_cost
            profit_report.save()

    class Meta:
        ordering = ["-date"]  # ✅ Show latest sales first

### ✅ SALE ITEM MODEL (Tracks multiple products per sale) ###
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")  # ✅ Link multiple items to a sale
    product = models.ForeignKey(Product, on_delete=models.CASCADE, default=1)  
    quantity = models.PositiveIntegerField()
    price_per_piece = models.DecimalField(max_digits=10, decimal_places=2)

    def total_price(self):
        """ Compute total price for this item """
        return self.quantity * self.price_per_piece

    total_price.short_description = "Total Price"

    def __str__(self):
        return f"{self.quantity} x {self.product.name} @ {self.price_per_piece}"

    def save(self, *args, **kwargs):
        """Reduce stock when sale is created or updated"""
        if not self.pk:  # Only reduce stock on first save
            self.product.stock_quantity -= self.quantity
        else:
            old_item = SaleItem.objects.get(pk=self.pk)
            stock_change = old_item.quantity - self.quantity  # Get the stock difference
            self.product.stock_quantity += stock_change
        self.product.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Restore stock when sale item is deleted"""
        self.product.stock_quantity += self.quantity
        self.product.save()
        super().delete(*args, **kwargs)


### ✅ Payment - Tracks Payments & Updates Sale ###
class Payment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} for Sale #{self.sale.id}"

    def save(self, *args, **kwargs):
        """Update sale payment status when a new payment is added"""
        super().save(*args, **kwargs)

        self.sale.amount_paid += self.amount  # Increase total amount paid
        self.sale.save()  # Recalculate balance and payment status
