# src/forms/models.py (Versão CONSOLIDADA)

from django.db import models
from src.company.models import Company

# Não precisamos mais do JSONField
# from django.contrib.postgres.fields import JSONField

# --- Choices para o Modelo ---

PLAN_CHOICES = [
    ('individual', 'Individual'),
    ('family', 'Family'),
]

TYPE_CHOICES = [
    ('Medicare', 'Medicare'),
    ('Dental', 'Dental'),
    ('Life', 'Life'),
    ('Health', 'Health'),
    ('Vision', 'Vision'),
]

INCOME_CHOICES = [
    ('0k-15k', '0k-15k'),
    ('15k-25k', '15k-25k'),
    ('30k-50k', '30k-50k'),
    ('50k-75k', '50k-75k'),
    ('75k-100k', '75k-100k'),
]

FORM_TYPE_CHOICES = [
    ("homepage", "Homepage Form"),
    ("referral", "Referral Friend Form"),
    ("appointment", "Appointment Form"),
    ("contact", "Contact Form"),
    ("careers", "Careers Form"),
]


class FormSubmission(models.Model):
    # Relações
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="form_submissions")
    profile = models.ForeignKey("users.Profile", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="form_submissions")

    # Informações básicas do formulário/cliente (da FormSubmission original + SheetData)
    formType = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, db_index=True)
    first_name = models.CharField(max_length=120, null=True, blank=True)
    last_name = models.CharField(max_length=120, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=40, null=True, blank=True)

    # Dados de Cobertura (da SheetData)
    zipCode = models.CharField(max_length=100, blank=True, null=True)
    coverageType = models.CharField(max_length=20, choices=PLAN_CHOICES, null=True,
                                    blank=True)  # Alterado para null=True, blank=True
    insuranceCoverage = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True,
                                         blank=True)  # Alterado para null=True, blank=True
    householdIncome = models.CharField(max_length=20, choices=INCOME_CHOICES, null=True, blank=True)

    # Dados Pessoais Adicionais (da SheetData)
    dob = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    # Dados do Indicador (Referrer) (da SheetData)
    referrerFirstName = models.CharField(max_length=255, blank=True, null=True)
    referrerEmail = models.EmailField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)  # datetime da SheetData é o created_at

    # NOTA: O campo 'extra' FOI REMOVIDO!

    class Meta:
        verbose_name = "Form Submission"
        verbose_name_plural = "Form Submissions"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.formType} – {self.email or self.phone or 'no contact'} @ {self.created_at:%Y-%m-%d}"