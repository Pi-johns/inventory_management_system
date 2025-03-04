from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import Group
from shops.models import Shop  # Import Shop model

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('manager', 'Manager'),
        ('seller', 'Seller'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='seller')
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")  # ✅ Changed from "sellers" to "users"

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_seller(self):
        return self.role == 'seller'

    def save(self, *args, **kwargs):
        """Fix recursion issue when updating is_staff and assigning Manager group"""
        if not self.pk:  # If user is being created for the first time, save normally
            super().save(*args, **kwargs)

        # ✅ Auto-set Managers as staff
        if self.is_manager and not self.is_staff:
            self.is_staff = True
            super().save(update_fields=["is_staff"])  # ✅ Avoid infinite recursion

        # ✅ Ensure user is in the "Manager" group
        if self.is_manager:
            manager_group, _ = Group.objects.get_or_create(name="Manager")
            self.groups.add(manager_group)

        # ✅ Final save (only if needed)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"
