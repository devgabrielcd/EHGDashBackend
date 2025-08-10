from django.urls import path
from .views import CompanyListView, CompanyCreateView, CompanyDetailView

urlpatterns = [
    path('list/', CompanyListView.as_view(), name='company-list'),  # Listar empresas
    path('create/', CompanyCreateView.as_view(), name='company-create'),  # Criar uma empresa
    path('details/<int:pk>/', CompanyDetailView.as_view(), name='company-detail'),  # Detalhar, atualizar ou deletar uma empresa
]
