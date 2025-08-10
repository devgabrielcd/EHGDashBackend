from django.contrib import admin

from src.users.models import Profile, UserType, UserRole


@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_type',
    )


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_role',
    )


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
