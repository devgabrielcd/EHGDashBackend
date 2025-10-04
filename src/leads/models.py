from django.db import models
from src.company.models import Company
from src.users.models import Profile
from src.products.models import ProductDetail, PLAN_CHOICES,TYPE_CHOICES



INCOME_CHOICES = [
    ('0k-15k', '0k-15k'),
    ('15k-25k', '15k-25k'),
    ('30k-50k', '30k-50k'),
    ('50k-75k', '50k-75k'),
    ('75k-100k', '75k-100k'),
]

FORM_TYPE_CHOICES = [
    ('homepage', 'Homepage Form'),
    ('referral', 'Referral Friend Form'),
    ('appointment', 'Appointment Form'),
    ("contact", "Contact Form"),
    ("careers", "Careers Form"),
]

class Lead(models.Model):

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='lead_submissions')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='leads', blank=True, null=True)
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, default='homepage')
    created_at = models.DateTimeField(auto_now_add=True)
    coverage_type = models.CharField(max_length=20, choices=PLAN_CHOICES)
    insurance_coverage = models.CharField(max_length=20, choices=TYPE_CHOICES)
    household_income = models.CharField(max_length=20, choices=INCOME_CHOICES)

    def __str__(self):
        company_name = self.company.name if self.company else 'N/A'
        return f"Lead: {self.profile.full_name} ({self.form_type} - {company_name})"

    class Meta:
        verbose_name = "Form Lead"
        verbose_name_plural = "Form Leads"
        ordering = ['-created_at']

class Referrer(models.Model):
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, related_name='referrer_info')
    first_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"Referral: {self.first_name} para Lead {self.lead.id}"

    class Meta:
        verbose_name = "Referral"
        verbose_name_plural = "Referrals"