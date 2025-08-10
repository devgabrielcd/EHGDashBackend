# src/sheets/admin.py
from django.contrib import admin
from .models import SheetData

@admin.register(SheetData)
class SheetDataAdmin(admin.ModelAdmin):
    list_display = (
         'id', 'company', 'firstName', 'lastName', 'email', 'phone', # Mantenha campos mais importantes no início
         'formType', # Adicionado aqui para aparecer na lista
         'zipCode', 'city', 'state', 'address', 'coverageType', 'insuranceCoverage',
         'householdIncome', 'dob', 'datetime', 'referrerFirstName', 'referrerEmail' # Adicionados ao final da linha
    )
    list_filter = (
        'formType', # Adicionado aqui para filtrar por tipo de formulário
        'company', # Bom ter a empresa também para filtrar
        'coverageType', 'insuranceCoverage', 'householdIncome',
        'state', 'datetime'
    )
    search_fields = (
        'firstName', 'lastName', 'email', 'phone',
        'city', 'state', 'zipCode',
        'formType', # Adicionado aqui para pesquisa por tipo de formulário
        'company__name', 'referrerFirstName', 'referrerEmail' # Adicionados ao final da linha
    )
    ordering = ('-datetime',)
    readonly_fields = ('datetime',)
    fieldsets = (
        ('General Information', {
            'fields': ('company', 'formType', 'datetime') # Adicionado formType aqui no fieldset de informações gerais
        }),
        ('Personal Details', {
            'fields': ('firstName', 'lastName', 'dob', 'email', 'phone', 'address', 'city', 'state', 'zipCode')
        }),
        ('Plan Details', {
            'fields': ('coverageType', 'insuranceCoverage', 'householdIncome')
        }),
        ('Referrer Details', { # Novo fieldset para os detalhes do indicador
            'fields': ('referrerFirstName', 'referrerEmail')
        })
        # Se você adicionou campos específicos de appointment (ex: appointment_date),
        # pode criar um novo fieldset para eles ou adicioná-los em 'Personal Details'.
        # Exemplo:
        # ('Appointment Details', {
        #     'fields': ('appointment_date', 'appointment_time', 'appointment_method', 'contact_preference', 'user_suggestions')
        # }),
    )