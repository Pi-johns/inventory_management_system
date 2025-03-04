from django.urls import path
from .views import all_notifications

app_name = "notifications"

urlpatterns = [
    path("all/", all_notifications, name="all_notifications"),
]
