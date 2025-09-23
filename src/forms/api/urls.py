# forms/api/urls.py
from django.urls import path
from .views import form_list_create_api, form_detail_api

urlpatterns = [
    path("forms/", form_list_create_api, name="forms-list-create"),
    path("forms/<int:pk>/", form_detail_api, name="forms-detail"),
]
