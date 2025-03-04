from django.db import models
from datetime import timedelta

class Shop(models.Model):
    name = models.CharField(max_length=255, unique=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class BusinessPeriodConfig(models.Model):
    PERIOD_CHOICES = [
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
    ]

    period_value = models.PositiveIntegerField(default=1)  # Default: 1 (Can be any number)
    period_type = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='weeks')  
    last_calculation_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.period_value} {self.get_period_type_display()}"

    def next_calculation_date(self):
        """Calculates the next period end date based on the settings."""
        if self.period_type == 'days':
            return self.last_calculation_date + timedelta(days=self.period_value)
        elif self.period_type == 'weeks':
            return self.last_calculation_date + timedelta(weeks=self.period_value)
        elif self.period_type == 'months':
            return self.last_calculation_date + timedelta(days=30 * self.period_value)  # Approximation
        elif self.period_type == 'years':
            return self.last_calculation_date + timedelta(days=365 * self.period_value)  # Approximation

class BusinessPerformanceHistory(models.Model):
    period_start = models.DateField()
    period_end = models.DateField()
    total_cash_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_credit_sales = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_partial_payments = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    carried_forward_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"Performance: {self.period_start} to {self.period_end}"
