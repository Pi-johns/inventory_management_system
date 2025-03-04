from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Expense(models.Model):
    """Tracks business expenses manually entered by managers"""
    CATEGORY_CHOICES = [
        ("RENT", "Rent"),
        ("UTILITIES", "Utilities"),
        ("SUPPLIES", "Supplies"),
        ("SALARIES", "Salaries"),
        ("DAMAGED_GOODS", "Loss Due to Damage"),
        ("OTHER", "Other"),
    ]

    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="OTHER")
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date_recorded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - ${self.amount} ({self.get_category_display()})"
