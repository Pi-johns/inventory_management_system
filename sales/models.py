from django.db import models
from django.contrib.auth import get_user_model
from shops.models import Shop
from inventory.models import Product
from accounts.models import CustomUser

User = get_user_model()
class Sale(models.Model):
    """Main sale transaction"""
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sales")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="sales")
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=15, blank=True, null=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Cached total
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Cached balance
    last_edited = models.DateTimeField(auto_now=True)  # Automatically updates on save
    period_processed = models.BooleanField(default=False)  # ✅ Ensures it is locked in reports

    STATUS_CHOICES = [
        ("Active", "Active"),  # Ongoing sale
        ("Completed", "Completed"),  # Successfully completed sale
        ("Damaged", "Damaged"),  # Sale marked as damaged
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Active")

    PAYMENT_STATUS_CHOICES = [
        ("paid", "Paid"),
        ("partial", "Partial Payment"),
        ("credit", "Credit"),
    ]
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="credit"
    )

    sale_date = models.DateTimeField(auto_now_add=True)

    def update_totals(self):
        """Recalculate total sale amount, balance, and payment status safely"""
        if self.status == "Damaged":
            print(f"DEBUG - Sale {self.id} is marked as Damaged. Skipping total updates.")
            return  # No need to update a damaged sale

        try:
            sale_items = self.items.all()
            self.grand_total = sum(item.total_price for item in sale_items) if sale_items.exists() else 0
            self.balance = self.grand_total - self.amount_paid

            # Determine payment status
            if self.balance <= 0:
                self.payment_status = "paid"
                self.balance = 0  # Ensure no negative balance
            elif self.amount_paid > 0:
                self.payment_status = "partial"
            else:
                self.payment_status = "credit"

            print(f"DEBUG - Sale {self.id}: grand_total={self.grand_total}, balance={self.balance}, status={self.payment_status}")

        except Exception as e:
            print(f"ERROR in update_totals(): {e}")

    def save(self, *args, **kwargs):
        """Ensure totals update on every save, with debugging"""
        if self.status != "Damaged":
            try:
                self.update_totals()
            except Exception as e:
                print(f"ERROR in update_totals(): {e}")  # Print error
        super().save(*args, **kwargs)  # Save instance

    def __str__(self):
        return f"Sale #{self.id} - {self.customer_name} ({self.payment_status}) [{self.status}]"
        
    def calculate_profit(self):
        """Calculate profit based on sale details, ignoring damaged sales."""
        if self.status == "Damaged":
            print(f"DEBUG - Sale {self.id} is damaged. Profit calculation skipped.")
            return 0  # No profit from damaged sales

        total_cost = sum(item.product.price * item.quantity for item in self.saleitem_set.all())
        return self.grand_total - total_cost

class SaleItem(models.Model):
    """Represents each product sold in a sale"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sale_items")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Used `price`, as requested
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        """Auto-calculate total price when saving"""
        self.total_price = self.quantity * self.price
        super().save(*args, **kwargs)

        # Track changes in sale totals before saving
        old_totals = (self.sale.grand_total, self.sale.balance, self.sale.payment_status)
        self.sale.update_totals()
        new_totals = (self.sale.grand_total, self.sale.balance, self.sale.payment_status)

        # Save sale only if something actually changed
        if old_totals != new_totals:
            self.sale.save(update_fields=["grand_total", "balance", "payment_status"])

    def delete(self, *args, **kwargs):
        """Ensure sale totals update when an item is deleted"""
        super().delete(*args, **kwargs)
        self.sale.update_totals()
        self.sale.save()

    def __str__(self):
        return f"{self.product.name} x {self.quantity} for Sale #{self.sale.id}"


class Payment(models.Model):
    """Payment model to track sale payments"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} for Sale #{self.sale.id}"

    def save(self, *args, **kwargs):
        """Update sale payment status when a new payment is added"""
        super().save(*args, **kwargs)  # Save payment first

        # Update total paid amount
        old_totals = (self.sale.amount_paid, self.sale.balance, self.sale.payment_status)
        self.sale.amount_paid = sum(payment.amount for payment in self.sale.payments.all())
        self.sale.update_totals()
        new_totals = (self.sale.amount_paid, self.sale.balance, self.sale.payment_status)

        # Save only if something actually changed
        if old_totals != new_totals:
            self.sale.save(update_fields=["amount_paid", "balance", "payment_status"])

        # Debugging
        print(f"DEBUG - Payment saved: {self.amount} for Sale {self.sale.id}")
        print(f"DEBUG - Updated Sale {self.sale.id} new amount_paid: {self.sale.amount_paid}")


# ==========================
# NEW MODEL: DAMAGED GOODS
# ==========================
class DamagedGoods(models.Model):
    """Tracks damaged goods returned from sales"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="damaged_goods")
    quantity = models.PositiveIntegerField()
    reason = models.TextField(blank=True, null=True)  # Optional reason for damage
    seller = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    date_damaged = models.DateTimeField(auto_now_add=True)
    total_loss = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
   
    def save(self, *args, **kwargs):
        """Automatically calculate total loss before saving."""
        self.total_loss = self.quantity * self.product.entry_price  # Assuming entry_price exists
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} damaged"

# ==========================
# NEW MODEL: CREDIT TRANSACTION
# ==========================
class CreditTransaction(models.Model):
    """Tracks credit payments made by customers over time."""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="credit_transactions")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Credit Payment of {self.amount_paid} for Sale #{self.sale.id} on {self.payment_date}"


# ==========================
# NEW MODEL: CASH TRANSACTION
# ==========================
class CashTransaction(models.Model):
    """Records cash payments for sales."""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="cash_transactions")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Cash Payment of {self.amount_paid} for Sale #{self.sale.id} on {self.payment_date}"
