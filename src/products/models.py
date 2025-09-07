from django.db import models
from src.company.models import Company

# Reuso do padrão do sheets (choices simples)
PLAN_CHOICES = [
    ("individual", "Individual"),
    ("family", "Family"),
]

TYPE_CHOICES = [
    ("Medicare", "Medicare"),
    ("Dental", "Dental"),
    ("Life", "Life"),
    ("Health", "Health"),
    ("Vision", "Vision"),
]


class Product(models.Model):
    """
    Produto “enxuto”, combinando Plan Type (coverageType) e Insurance Coverage (insuranceCoverage),
    e opcionalmente atrelado a uma Company.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True)

    # Nome curto/identificador (ex.: “Health – Individual”, “Dental – Family”)
    name = models.CharField(max_length=150)

    # Iguais ao sheets (choices)
    coverageType = models.CharField(max_length=20, choices=PLAN_CHOICES)
    insuranceCoverage = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # Flags básicas
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ("-created_at",)
        # Evita duplicidade óbvia dentro da mesma empresa
        unique_together = [("company", "name", "coverageType", "insuranceCoverage")]

    def __str__(self):
        base = f"{self.name} ({self.insuranceCoverage} / {self.coverageType})"
        return f"{self.company} – {base}" if self.company else base
