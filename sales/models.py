from django.db import models
from accounts.models import CustomUser  # Seller reference
from inventory.models import Product
from shops.models import Shop
from django.utils.timezone import now



class Sale(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'seller'})
    date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    customer_name = models.CharField(max_length=100, blank=True, null=True)
    customer_phone = models.CharField(max_length=15, blank=True, null=True)
    is_credit = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Sale #{self.id} by {self.seller} on {self.date}"

    def amount_paid(self):
        """Get total amount paid for this sale"""
        return sum(payment.amount for payment in self.payments.all())

    def amount_due(self):
        """Calculate remaining balance"""
        return self.total_amount - self.amount_paid()

    def update_payment_status(self):
        """Update is_paid based on payments"""
        self.is_paid = self.amount_due() <= 0
        self.save()

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.quantity * self.selling_price

    def __str__(self):
        return f"{self.quantity} x {self.product.name} at {self.selling_price}"

    def save(self, *args, **kwargs):
        """Reduce stock when sale is created or updated"""
        if not self.pk:  # Only reduce stock on first save
            self.product.quantity -= self.quantity
            self.product.save()
        else:
            # Handle updating existing sale items (if quantity changes)
            old_item = SaleItem.objects.get(pk=self.pk)
            stock_change = old_item.quantity - self.quantity  # Get the stock difference
            self.product.quantity += stock_change
            self.product.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Restore stock when sale item is deleted"""
        self.product.quantity += self.quantity
        self.product.save()
        super().delete(*args, **kwargs)

class CreditSale(models.Model):
    sale = models.OneToOneField(Sale, on_delete=models.CASCADE, related_name="credit_sale")
    paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(blank=True, null=True)

    def remaining_balance(self):
        """Calculate remaining balance for this credit sale"""
        return self.sale.amount_due()

    def update_credit_status(self):
        """Update payment status when payments are made"""
        self.paid = self.remaining_balance() <= 0
        if self.paid:
            self.paid_date = now()
        self.save()

    def __str__(self):
        return f"Credit Sale #{self.sale.id} - {'Paid' if self.paid else 'Unpaid'}"
    

class Payment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} for Sale #{self.sale.id}"

    def save(self, *args, **kwargs):
        """Update sale payment status when a new payment is added"""
        super().save(*args, **kwargs)
        self.sale.update_payment_status()
        if self.sale.is_credit:
            self.sale.credit_sale.update_credit_status()
