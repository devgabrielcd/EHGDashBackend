# src/forms/models.py
from django.db import models
from src.company.models import Company
from django.contrib.postgres.fields import JSONField  # se usar Postgres <3.1
# Em Django moderno, use models.JSONField

FORM_TYPE_CHOICES = [
    ("homepage", "Homepage Form"),
    ("referral", "Referral Friend Form"),
    ("appointment", "Appointment Form"),
    ("contact", "Contact Form"),
    ("careers", "Careers Form"),
]

class FormSubmission(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="form_submissions")
    profile = models.ForeignKey("users.Profile", on_delete=models.SET_NULL, null=True, blank=True, related_name="form_submissions")
    formType = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, db_index=True)
    first_name = models.CharField(max_length=120, null=True, blank=True)
    last_name = models.CharField(max_length=120, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=40, null=True, blank=True)
    coverageType = models.CharField(max_length=20, null=True, blank=True)
    insuranceCoverage = models.CharField(max_length=20, null=True, blank=True)
    extra = models.JSONField(default=dict, blank=True)  # se Django 3.1+, senão JSONField do postgres
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Form Submission"
        verbose_name_plural = "Form Submissions"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.formType} – {self.email or self.phone or 'no contact'} @ {self.created_at:%Y-%m-%d}"
