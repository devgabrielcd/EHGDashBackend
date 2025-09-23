from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from src.forms.models import FORM_TYPE_CHOICES

from src.company.models import Company
from src.products.models import PLAN_CHOICES, TYPE_CHOICES

class UserType(models.Model):
    user_type = models.CharField(max_length=30)

    def __str__(self):
        return f'{self.user_type}'


class UserRole(models.Model):
    user_role = models.CharField(max_length=30)

    def __str__(self):
        return f'{self.user_role}'


class CustomerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user_type__user_type='Customer')


class EmployeeManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user_type__user_type='Employee')


PHONE_TYPE = (
    ('mobile', 'mobile'),
    ('home', 'home'),
    ('work', 'work'),
)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    user_type = models.ForeignKey(UserType, on_delete=models.DO_NOTHING, null=True, blank=True)
    user_role = models.ForeignKey(UserRole, on_delete=models.DO_NOTHING, null=True, blank=True)
    first_name = models.CharField(max_length=40, null=True, blank=True)
    middle_name = models.CharField(max_length=40, null=True, blank=True)
    last_name = models.CharField(max_length=40, null=True, blank=True)
    phone_number = models.CharField(max_length=12, null=True, blank=True)
    phone_number_type = models.CharField(max_length=6, choices=PHONE_TYPE, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    # theme = models.CharField(max_length=6, choices=THEME, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    signed_date = models.DateField(null=True, blank=True)
    image = models.FileField(null=True, blank=True)
    objects = models.Manager()
    employee_users = EmployeeManager()  # eg. Employees.employee_users.all()
    customer_users = CustomerManager()  # eg. Employees.customer_users.all()
    company = models.ForeignKey(Company, on_delete=models.DO_NOTHING, null=True, blank=True) # 👈 ADICIONE ESTA LINHA
    coverageType = models.CharField(max_length=20, choices=PLAN_CHOICES, null=True, blank=True)
    insuranceCoverage = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    formType = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES, null=True, blank=True)

    def __str__(self):
        return f'{self.user_type} - {self.first_name} {self.last_name}'

    @property
    def full_name(self):

        if not self.first_name:
            return f'Name not filled'

        if self.first_name and self.middle_name and self.last_name:
            return f'{self.first_name} {self.middle_name} {self.last_name}'

        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'


def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            # role=instance.role,
            # first_name=instance.first_name or "",
            # last_name=instance.last_name or "",
            # email=instance.email or ""
        )


post_save.connect(create_profile, sender=User)



