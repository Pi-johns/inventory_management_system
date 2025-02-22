from django.contrib.auth.models import AbstractUser
from django.db import models


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

