# sheets/urls.py
from django.urls import path
from .views import SheetDataListAPIView

urlpatterns = [
    path('sheet-data/', SheetDataListAPIView.as_view(), name='sheet_data_list'),
]