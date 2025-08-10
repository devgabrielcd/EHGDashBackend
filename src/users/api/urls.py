from django.urls import path

from .views import DetailUserAPIView, detail_user_api

urlpatterns = [
    path('detail-user/<int:pk>/', detail_user_api, name='detail-user'),
]
