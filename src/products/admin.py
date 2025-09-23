from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "company",
        "insuranceCoverage",
        "coverageType",
        "formType",
        "is_active",
        "created_at",
    )
    list_filter = (
        "company",
        "insuranceCoverage",
        "coverageType",
        "formType",
        "is_active",
    )
    search_fields = (
        "name",
        "company__name",
    )
    autocomplete_fields = ("company",)
    ordering = ("-created_at",)
