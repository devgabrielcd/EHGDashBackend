from django.db import models
from django.urls import reverse


class Company(models.Model):
    name = models.CharField(max_length=70, help_text="Company name")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('home')
