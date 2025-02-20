from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('manager', 'Manager'),
        ('seller', 'Seller'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='seller')

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_seller(self):
        return self.role == 'seller'

    def __str__(self):
        return f"{self.username} ({self.role})"


class Seller(models.Model):
    """Represents a seller who is assigned to a specific shop."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shop = models.ForeignKey("shops.Shop", on_delete=models.CASCADE, related_name="sellers")  # ✅ Lazy import
    phone = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.shop.name}"
