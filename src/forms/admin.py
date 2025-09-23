from django.contrib import admin
from src.forms.models import FormSubmission


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    # Mostra apenas os campos que existem no modelo
    list_display = (
        "id",
        "company",
        "profile",  # Adicionado o campo 'profile' para visualização
        "formType",
        "created_at",
    )
    list_filter = ("company", "formType", "created_at")
    search_fields = ("formType",)  # 'formType' é o único campo de texto que sobrou
    date_hierarchy = "created_at"

    # Adicionado autocomplete_fields para o campo 'profile',
    # pois é uma ForeignKey e melhora a experiência de busca no admin
    autocomplete_fields = ("profile",)