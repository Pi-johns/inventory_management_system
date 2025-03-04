from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    low_stock_threshold = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def update_stock(self, quantity):
        """
        Safely updates stock by decreasing the given quantity.
        Logs stock changes in `StockLog`.
        """
        if quantity > self.stock_quantity:
            raise ValueError(f"Not enough stock for {self.name}. Available: {self.stock_quantity}")
        
        self.stock_quantity -= quantity
        self.save()
        StockLog.objects.create(
            product=self,
            change=-quantity,
            description=f"Sold {quantity} units"
        )

    def is_low_stock(self):
        """Check if product stock is below the threshold."""
        return self.stock_quantity <= self.low_stock_threshold  # ✅ Now uses `stock_quantity`

    def __str__(self):
        return f"{self.name} ({self.stock_quantity} left)"  # ✅ Display correct stock

class StockLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    change = models.IntegerField()  # Positive for addition, Negative for deduction
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.change} units - {self.timestamp}"
