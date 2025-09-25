from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from src.company.models import Company

User = get_user_model()

class ActivityLog(models.Model):
    # quem disparou
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="activities_as_actor")
    # alvo principal da ação (ex.: user editado/deletado)
    target_user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="activities_as_target")
    company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL)

    # ação “curta” padronizada
    action = models.CharField(max_length=64)  # ex.: user.create, user.update, user.delete, password.change, prefs.update, forms.submit
    # texto amigável pronto p/ UI (opcional, mas útil)
    message = models.TextField(blank=True, default="")

    # metadados livres (ex.: campos alterados, formType, ip, etc.)
    meta = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["action"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        who = (self.actor and self.actor.username) or "system"
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {who} -> {self.action}"
