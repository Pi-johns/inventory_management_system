from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    """
    Stores system notifications for users.
    
    - If `user` is set, the notification is targeted to that user.
    - If `user` is null, it can be used as a global notification.
    - The optional `url` field links the notification to a related page.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    message = models.TextField()
    url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Optional URL for more details or to take an action."
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        recipient = self.user.username if self.user else "All Users"
        return f"Notification for {recipient} - {self.message[:50]}"

    class Meta:
        ordering = ['-created_at']
