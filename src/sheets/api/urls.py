# src/sheets/api/urls.py
from django.urls import path
from .views import SheetDataListAPIView, SheetStatsAPIView

urlpatterns = [
    path('sheet-data/', SheetDataListAPIView.as_view(), name='sheet_data_list'),
    path('stats/', SheetStatsAPIView.as_view(), name='sheet_stats'),  # 👈 novo
]
