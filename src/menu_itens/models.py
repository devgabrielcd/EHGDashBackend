from django.db import models
from django.core.exceptions import ValidationError

# Ajuste o caminho abaixo se seu app não se chama exatamente "user"
from src.users.models import UserType, UserRole


class MenuItem(models.Model):
    key = models.SlugField(unique=True)                         # ex: "dashboard", "settings"
    label = models.CharField(max_length=100, blank=True, null=True)                    # ex: "Dashboard"
    icon = models.CharField(max_length=100, blank=True, null=True)  # opcional: nome do ícone no front
    path = models.CharField(max_length=255, blank=True, null=True)  # ex: "/dashboard"
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=True)
    feature_flag = models.CharField(max_length=100, blank=True, null=True)  # opcional

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return (self.label or self.key or f"menuitem-{self.pk}")


class RoleMenuItem(models.Model):
    """
    Associa um MenuItem a um UserType e/ou UserRole, com ordenação e visibilidade.
    Pelo menos UM entre user_type e user_role deve ser definido.
    """
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="role_links")
    user_type = models.ForeignKey(UserType, on_delete=models.CASCADE, null=True, blank=True)
    user_role = models.ForeignKey(UserRole, on_delete=models.CASCADE, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]
        # Observação: unique_together com null permite múltiplos NULLs; está ok para nossa necessidade.
        unique_together = ("menu_item", "user_type", "user_role")

    def clean(self):
        if not self.user_type and not self.user_role:
            raise ValidationError("Defina ao menos user_type OU user_role para RoleMenuItem.")

    def __str__(self):
        parts = []
        if self.user_type:
            parts.append(f"UT:{self.user_type}")
        if self.user_role:
            parts.append(f"UR:{self.user_role}")
        target = " | ".join(parts) if parts else "UNBOUND"
        return f"{target} → {self.menu_item.key}"
