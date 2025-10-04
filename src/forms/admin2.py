from django.contrib import admin
from .models import FormSubmission

@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "formType",
        "first_name",
        "last_name",
        "email",
        "phone",
        "address",
        "city",
        "state",
        "zipCode",
        "householdIncome",
        "selected_product",
        "company",
        "profile",
        "created_at",
    )
    list_filter = ("formType", "company", "householdIncome")
    search_fields = (
        "first_name", "last_name", "email", "phone",
        "address", "city", "state", "zipCode",
        "referrerFirstName", "referrerEmail",
    )
    readonly_fields = ("created_at",)
    raw_id_fields = ("company", "profile", "selected_product")
