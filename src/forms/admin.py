# src/forms/admin.py

from django.contrib import admin
from .models import FormSubmission

@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    # Campos exibidos na lista principal (tabela)
    list_display = (
        "id",
        "formType",
        "first_name",
        "last_name",
        "email",
        "phone",
        "coverageType",
        "householdIncome",
        "created_at",
        "company",
    )

    # Campos pelos quais é possível filtrar a lista
    list_filter = (
        "formType",
        "coverageType",
        "insuranceCoverage",
        "householdIncome", # Agora funciona porque o campo existe!
        "created_at",
        "company",
    )

    # Campos pelos quais é possível fazer busca textual
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "zipCode",
        "address",
        "city",
        "referrerFirstName",
    )

    # Campos que usam um campo de texto em vez de um seletor para ForeignKey
    raw_id_fields = (
        "company",
        "profile",
    )

    # Organização dos campos na página de edição/criação
    fieldsets = (
        ('Informações da Submissão', {
            'fields': ('formType', 'company', 'profile', 'created_at',),
        }),
        ('Dados de Contato e Pessoais', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'dob'),
        }),
        ('Dados de Endereço', {
            'fields': ('zipCode', 'address', 'city', 'state'),
        }),
        ('Dados de Cobertura e Renda', {
            'fields': ('coverageType', 'insuranceCoverage', 'householdIncome'),
        }),
        ('Dados do Indicador (Referrer)', {
            # Note a alteração do nome aqui para coincidir com o modelo
            'fields': ('referrerFirstName', 'referrerEmail'),
            'classes': ('collapse',), # Opcional: torna a seção recolhível
        }),
    )

    # Torna o 'created_at' e 'profile' (se aplicável) somente leitura
    readonly_fields = ('created_at',)