from django.contrib import admin
from .models import ProductDetail


@admin.register(ProductDetail)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",

    )
    list_filter = (

    )
    search_fields = (
        "name",
        "company__name",
    )


