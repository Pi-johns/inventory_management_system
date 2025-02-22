import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification
from accounts.models import CustomUser
from django.shortcuts import render, redirect


def send_notification(user=None, message=""):
    """Send a notification to a specific user or broadcast to all Managers & Superadmins."""
    if user:
        # Create a notification for a specific user (e.g., Seller)
        Notification.objects.create(user=user, message=message)
        group_name = f'notifications_{user.id}'
    else:
        # Broadcast to all Managers & Superadmins
        Notification.objects.create(user=None, message=message)
        group_name = 'notifications_admins'
    
    # Get the channel layer for WebSockets
    channel_layer = get_channel_layer()

    if channel_layer is None:
        print("⚠️ ERROR: Channel layer is not available. Notification not sent.")
        return  # Prevents crash

    # Send the notification via WebSockets (if possible)
    async_to_sync(channel_layer.group_send)(
        group_name,
        {"type": "send_notification", "message": message}
    )


@login_required
def get_notifications(request):
    """Fetch notifications for the logged-in user."""
    if request.user.role in ['superadmin', 'manager']:
        notifications = Notification.objects.filter(user__isnull=True) | Notification.objects.filter(user=request.user)
    else:
        notifications = Notification.objects.filter(user=request.user)

    return render(request, "notifications/notification_list.html")

@login_required
def mark_as_read(request):
    """Mark all notifications as read for the logged-in user."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect("notifications_mark_as_read")

