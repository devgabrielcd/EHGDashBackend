from django.contrib import admin
from src.users.models import Profile, UserType, UserRole


@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_type',)
    search_fields = ('user_type',)  # << necessário p/ autocomplete


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_role',)
    search_fields = ('user_role',)  # << necessário p/ autocomplete


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'first_name',
        'last_name',
        'phone_number',
        'email',
        'user_type',
        'user_role',
    )
    # opcional, mas ajuda:
    search_fields = (
        'user__username',
        'first_name',
        'last_name',
        'email',
        'phone_number',
    )
