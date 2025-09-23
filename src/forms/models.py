# src/forms/models.py
from django.db import models
from src.company.models import Company

# ——— Choices ———
FORM_TYPE_CHOICES = [
    ("homepage", "Homepage Form"),
    ("referral", "Referral Friend Form"),
    ("appointment", "Appointment Form"),
    ("contact", "Contact Form"),
    ("careers", "Careers Form"),
]


class FormSubmission(models.Model):

    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="form_submissions")
    profile = models.ForeignKey("users.Profile", on_delete=models.CASCADE, null=True, blank=True, related_name="form_submissions", help_text="Vincule esta submissão ao perfil do usuário, se aplicável.")
    formType = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, db_index=True, help_text="Tipo de formulário submetido (igual aos tipos usados no site).")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Form Submission"
        verbose_name_plural = "Form Submissions"
        ordering = ("-created_at",)

    def __str__(self):
        # A representação do objeto agora se baseia apenas no tipo de formulário.
        # Caso precise do nome, você pode acessar pelo self.profile.
        return f"{self.formType} - Submetido em {self.created_at.strftime('%Y-%m-%d')}"