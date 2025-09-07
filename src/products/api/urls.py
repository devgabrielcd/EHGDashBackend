# src/products/api/urls.py
from django.urls import path

from .views import (
    products_list_create_api,   # GET (list) / POST (create)
    product_detail_api,         # GET / PATCH / DELETE
    product_choices_api,        # GET choices de coverageType/insuranceCoverage (opcional, mas útil)
)

app_name = "products_api"

urlpatterns = [
    path("", products_list_create_api, name="product-list-create"),
    path("<int:pk>/", product_detail_api, name="product-detail"),
    path("choices/", product_choices_api, name="product-choices"),
]
