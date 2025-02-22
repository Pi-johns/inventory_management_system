from django.db import models
from django.conf import settings
from shops.models import Shop  # Import Shop model

class Seller(models.Model):
    """Represents a seller assigned to a shop."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="sellers")  
    phone = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.shop.name}"
