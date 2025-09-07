# src/notifications/api/urls.py
from django.urls import path
from .views import (
    NotificationCountView,
    NotificationListView,
    NotificationMarkReadView,
)

app_name = "notifications_api"

urlpatterns = [
    path("count/", NotificationCountView.as_view(), name="count"),
    path("", NotificationListView.as_view(), name="list"),
    path("<int:pk>/read/", NotificationMarkReadView.as_view(), name="mark_read"),
]
