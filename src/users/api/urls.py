from django.urls import path
from .views import (
    users_list_create_api, user_detail_api, user_roles_list_api, user_types_list_api,
    detail_user_api, user_stats_api,
    change_password_api, user_preferences_api, user_sessions_api, user_session_delete_api,
    auth_session_api, auth_logout_api,  # 👈 NOVOS
)

urlpatterns = [
    path('users/', users_list_create_api, name='user-list-create'),
    path('users/<int:pk>/', user_detail_api, name='user-detail'),
    path('roles/', user_roles_list_api, name='user-roles-list'),
    path('types/', user_types_list_api, name='user-types-list'),
    path('detail-user/<int:pk>/', detail_user_api, name='detail-user'),
    path('user-stats/', user_stats_api, name='user-stats'),

    # Settings
    path('users/<int:pk>/preferences/', user_preferences_api, name='user-preferences'),
    path('users/<int:pk>/sessions/', user_sessions_api, name='user-sessions'),
    path('users/<int:pk>/sessions/<str:key>/', user_session_delete_api, name='user-session-delete'),
    # path('users/<int:pk>/integrations/', user_integrations_api, name='user-integrations'),
    path('users/change-password/', change_password_api, name='change-password'),

    # Auth helpers
    path('auth/session/', auth_session_api, name='auth-session'),
    path('auth/logout/', auth_logout_api, name='auth-logout'),
]
