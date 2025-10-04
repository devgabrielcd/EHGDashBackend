from django.db import models

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

class ProductDetail(models.Model):



    coverage_type = models.CharField(max_length=20, choices=PLAN_CHOICES)
    insurance_coverage = models.CharField(max_length=20, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.insurance_coverage} - {self.coverage_type}"

    class Meta:
        verbose_name = "Product Detail"
        verbose_name_plural = "Product Details"