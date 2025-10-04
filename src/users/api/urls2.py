# src/users/api/urls.py
from django.urls import path
from .views import (
    UsersAPIView, UserDetailAPIView,
    UserRolesAPIView, UserTypesAPIView,
    AuthSessionAPIView, AuthLogoutAPIView,
)

urlpatterns = [
    path("users/", UsersAPIView.as_view(), name="users"),
    path("users/<int:pk>/", UserDetailAPIView.as_view(), name="users-detail"),

    path("users/roles/", UserRolesAPIView.as_view(), name="users-roles"),
    path("users/types/", UserTypesAPIView.as_view(), name="users-types"),

    path("auth/session/", AuthSessionAPIView.as_view(), name="auth-session"),
    path("auth/logout/", AuthLogoutAPIView.as_view(), name="auth-logout"),
]
