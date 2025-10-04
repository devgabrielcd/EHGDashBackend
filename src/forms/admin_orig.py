# src/forms/admin.py

from django.contrib import admin
from .models import FormSubmission


# Importe o campo JSONField se estiver usando uma versão antiga do Django/Postgres
# Caso contrário, o Django 3.1+ lida com models.JSONField nativamente.

@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    # 1. list_display: Exibe os campos na lista de registros.
    # Usamos APENAS campos que existem no FormSubmission (ou métodos definidos aqui).
    list_display = (
        "id",
        "formType",
        "first_name",
        "last_name",
        "email",
        "phone",
        "coverageType",
        "insuranceCoverage",
        "company",
        "profile",
        "extra_address",  # Novo método para pegar 'address' do campo 'extra'
        "created_at",
    )

    # 2. list_filter: Permite filtrar por esses campos.
    # APENAS CAMPOS DO MODELO SÃO PERMITIDOS. Removemos 'householdIncome'.
    list_filter = (
        "formType",
        "coverageType",
        "insuranceCoverage",
        "created_at",
        "company",
    )

    # 3. raw_id_fields: Usa um campo de texto em vez de um seletor para chaves estrangeiras.
    # APENAS CAMPOS DO MODELO SÃO PERMITIDOS. Removemos 'selected_product'.
    raw_id_fields = (
        "company",
        "profile",
    )

    # 4. search_fields: Permite buscar nos campos de texto.
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "extra",  # Permite buscar em todo o conteúdo JSON
    )

    # 5. Métodos para extrair dados do JSONField 'extra' (Solução para os campos de endereço)
    def extra_address(self, obj):
        """Tenta retornar o endereço completo do campo JSON 'extra'."""
        # Acessa os campos, juntando 'address', 'city', 'state' e 'zipCode'
        address = obj.extra.get('address', '')
        city = obj.extra.get('city', '')
        state = obj.extra.get('state', '')
        zip_code = obj.extra.get('zipCode', '')

        # Constrói uma string de endereço formatada
        parts = [address, f"{city}, {state}" if city and state else city or state, zip_code]
        return " | ".join(filter(None, parts)) or '-'

    extra_address.short_description = 'Endereço (Extra)'
    extra_address.admin_order_field = 'extra'

    # Se quiser listar o Household Income, adicione um método similar e inclua em list_display:
    # def extra_household_income(self, obj):
    #     return obj.extra.get('householdIncome', '-')
    # extra_household_income.short_description = 'Renda'

    # Defina os campos a serem exibidos no formulário de edição/criação
    fieldsets = (
        (None, {
            'fields': (
                'formType', 'company', 'profile', 'first_name', 'last_name',
                'email', 'phone', 'coverageType', 'insuranceCoverage'
            )
        }),
        ('Dados Extras (JSON)', {
            'fields': ('extra',),
            'classes': ('collapse',),  # Opcional: faz a seção ser colapsável
        }),
    )

    # O campo 'extra' (JSONField) é um dicionário, então listamos ele em json_editor_fields:
    # Este é um recurso se você estiver usando um pacote admin que suporte edição de JSON (como django-json-editor)
    # Se não estiver usando um pacote específico, você pode usar um widget de textarea simples.
    # json_editor_fields = ('extra',) # Comente esta linha se não estiver usando um pacote JSON.

# admin.site.register(FormSubmission, FormSubmissionAdmin) # Se usar @admin.register, não precisa desta linha.