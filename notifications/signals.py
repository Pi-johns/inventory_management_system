from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from sales.models import Sale  # Make sure the Sale model is imported correctly
from .models import Notification

User = get_user_model()

@receiver(post_save, sender=Sale, weak=False)

def sale_created_notification(sender, instance, created, **kwargs):
    """
    When a new sale is recorded, create notifications for all managers and superadmins.
    """
    print(f"[DEBUG] post_save Signal Triggered for Sale {instance.id}, created={created}")
    if created:
        message = f"New sale recorded: Sale #{instance.id} for {instance.customer_name}."
        # Retrieve all managers and superadmins.
        managers = User.objects.filter(groups__name="Manager", is_active=True)
        superadmins = User.objects.filter(is_superuser=True)
        recipients = managers | superadmins
        for recipient in recipients.distinct():
            Notification.objects.create(
                user=recipient,
                message=message,
                url=f"/sales/edit/{instance.id}/"  # Example URL
            )
