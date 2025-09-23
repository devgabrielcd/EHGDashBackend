# src/users/urls.py
from django.urls import path
from .views import (
    users_list_create_api,
    user_detail_api,
    user_roles_list_api,
    user_types_list_api,
    detail_user_api,
    user_stats_api,
    # 👇 adicionar:
    change_password_api,
    user_preferences_api,
    user_sessions_api,
    user_session_delete_api,
    user_integrations_api,
    auth_session_api,
)

urlpatterns = [
    # CRUD
    path('users/', users_list_create_api, name='user-list-create'),
    path('users/<int:pk>/', user_detail_api, name='user-detail'),

    # Auxiliares
    path('roles/', user_roles_list_api, name='user-roles-list'),
    path('types/', user_types_list_api, name='user-types-list'),
    path('detail-user/<int:pk>/', detail_user_api, name='detail-user'),

    # KPIs
    path('user-stats/', user_stats_api, name='user-stats'),

    # ===== Settings =====
    path('users/change-password/', change_password_api, name='users-change-password'),  # SecurityCard
    path('users/<int:pk>/preferences/', user_preferences_api, name='users-preferences'),  # Appearance/Notifications
    path('users/<int:pk>/sessions/', user_sessions_api, name='users-sessions'),          # Sessions list
    path('users/<int:pk>/sessions/<str:key>/', user_session_delete_api, name='users-session-delete'),  # Revoke
    path('users/<int:pk>/integrations/', user_integrations_api, name='users-integrations'),  # Integrations

    path('auth/session/', auth_session_api, name='auth-session'),

]
