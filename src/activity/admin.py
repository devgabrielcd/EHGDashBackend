from django.contrib import admin
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "actor", "target_user", "company")
    list_filter = ("action", "company")
    search_fields = ("message", "meta")
    ordering = ("-created_at",)
