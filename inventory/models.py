from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255, unique=True)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    low_stock_threshold = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    

    @property
    def stock(self):
        """Alias for stock_quantity to avoid errors."""
        return self.stock_quantity

    def is_low_stock(self):
        """Check if product stock is below the threshold."""
        return self.stock <= self.low_stock_threshold  # Now using `stock`

    def __str__(self):
        return f"{self.name} ({self.stock} left)"
    
class StockLog(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    change = models.IntegerField()  # Positive for addition, Negative for deduction
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.change} units - {self.timestamp}"
