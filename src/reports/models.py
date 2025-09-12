import uuid
from django.db import models
from django.conf import settings

class Report(models.Model):
    class Status(models.TextChoices):
        READY = "Ready", "Ready"
        PROCESSING = "Processing", "Processing"
        FAILED = "Failed", "Failed"
        ACTIVE = "Active", "Active"
        DRAFT = "Draft", "Draft"
        SCHEDULED = "Scheduled", "Scheduled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100, db_index=True)      # ex.: Sales, Users, Retention...
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.READY, db_index=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="reports"
    )

    # Datas
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    # Payload/Config opcional (JSON)
    config = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} ({self.type})"
