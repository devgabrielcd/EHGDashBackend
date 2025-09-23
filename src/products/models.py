from django.db import models
from src.company.models import Company

# ===== Choices iguais ao sheets =====
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

FORM_TYPE_CHOICES = [
    ("homepage", "Homepage Form"),
    ("referral", "Referral Friend Form"),
    ("appointment", "Appointment Form"),
]


class Product(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, blank=True, null=True, related_name="products"
    )

    name = models.CharField(max_length=150)
    coverageType = models.CharField(max_length=20, choices=PLAN_CHOICES)
    insuranceCoverage = models.CharField(max_length=20, choices=TYPE_CHOICES)
    formType = models.CharField(
        max_length=20, choices=FORM_TYPE_CHOICES, default="homepage", db_index=True
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name", "coverageType", "insuranceCoverage", "formType"],
                name="uniq_product_company_name_coverage_line_formtype",
            )
        ]

    def __str__(self):
        base = f"{self.name} ({self.insuranceCoverage}/{self.coverageType}, {self.formType})"
        return f"{self.company} – {base}" if self.company else base
