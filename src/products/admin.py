from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "name",
        "coverageType",
        "insuranceCoverage",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_active",
        "company",
        "coverageType",
        "insuranceCoverage",
        "created_at",
    )
    search_fields = (
        "name",
        "company__name",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    fieldsets = (
        ("General", {
            "fields": ("company", "name", "is_active", "created_at"),
        }),
        ("Plan", {
            "fields": ("coverageType", "insuranceCoverage"),
        }),
    )
