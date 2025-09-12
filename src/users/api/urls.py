from django.urls import path


from .views import (
    users_list_create_api,
    user_detail_api,
    user_roles_list_api,
    user_types_list_api,
    detail_user_api, users_stats_api,
)

urlpatterns = [
    # CRUD de Usuários
    path('users/', users_list_create_api, name='user-list-create'),
    path('users/<int:pk>/', user_detail_api, name='user-detail'),

    # Endpoints auxiliares
    path('roles/', user_roles_list_api, name='user-roles-list'),
    path('types/', user_types_list_api, name='user-types-list'),

    path('users/stats/', users_stats_api, name='user-stats'),  # 👈 AQUI

    # Endpoint legado (mantido para compatibilidade)
    path('detail-user/<int:pk>/', detail_user_api, name='detail-user'),

]