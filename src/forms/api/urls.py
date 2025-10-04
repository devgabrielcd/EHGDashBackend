# src/forms/urls.py
from django.urls import path
from .views import FormSubmissionAPIView, FormSubmissionDetailAPIView

urlpatterns = [
    path("forms/", FormSubmissionAPIView.as_view(), name="forms"),
    path("forms/<int:pk>/", FormSubmissionDetailAPIView.as_view(), name="forms-detail"),
]
