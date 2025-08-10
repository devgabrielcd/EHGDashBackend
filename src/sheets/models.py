from django.db import models

from src.company.models import Company

# Opções para campos com escolhas
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

# Definir as opções para o tipo de formulário
FORM_TYPE_CHOICES = [
    ('homepage', 'Homepage Form'),
    ('referral', 'Referral Friend Form'),
    ('appointment', 'Appointment Form'),
]

class SheetData(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True)
    zipCode = models.CharField(max_length=100, blank=True, null=True)
    coverageType = models.CharField(max_length=20, choices=PLAN_CHOICES)
    insuranceCoverage = models.CharField(max_length=20, choices=TYPE_CHOICES)
    householdIncome = models.CharField(max_length=20, choices=INCOME_CHOICES)
    firstName = models.CharField(max_length=255, blank=True, null=True)
    lastName = models.CharField(max_length=255, blank=True, null=True)
    dob = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=100, blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    formType = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, default='homepage')
    # NOVOS CAMPOS PARA O INDICADOR (REFERRER)
    referrerFirstName=models.CharField(max_length=255, blank=True, null=True)
    referrerEmail=models.EmailField(blank=True, null=True)
    def __str__(self):
        return f"{self.firstName} {self.lastName} ({self.formType})"

    class Meta:
        verbose_name = "Sheet Data"
        verbose_name_plural = "Sheet Data"
