from django.contrib import admin
from .models import Company

class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name') # Adicione 'id' e quaisquer outros campos que você queira exibir

admin.site.register(Company, CompanyAdmin)