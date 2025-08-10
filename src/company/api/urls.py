from django.urls import path

from src.company.api.views import CompanyListAPIView, CompanyDetailsAPIView

urlpatterns = [
    path('list/', CompanyListAPIView.as_view(), name='company-list'),  # Listar empresas
    path('create/', CompanyListAPIView.as_view(), name='company-create'),  # Criar uma empresa
    path('details/<int:pk>/', CompanyDetailsAPIView.as_view(), name='company-detail'),  # Detalhar, atualizar ou deletar uma empresa
    path('edit/<int:pk>/', CompanyDetailsAPIView.as_view(), name='company-edit'),  # Detalhar, atualizar ou deletar uma empresa
    path('delete/<int:pk>/', CompanyDetailsAPIView.as_view(), name='company-delete'),  # Detalhar, atualizar ou deletar uma empresa
]