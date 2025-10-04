from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Profile, UserRole, UserType

User = get_user_model()

# Evita AlreadyRegistered
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("id", "username", "email", "is_active", "date_joined")
    list_filter = ("is_active",)
    search_fields = ("username", "email")
    readonly_fields = ("date_joined", "last_login")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "company",
        "user_role",
        "user_type",

    )
    search_fields = ("first_name", "last_name", "email", "phone_number")
    list_filter = ("company", "user_role", "user_type", )

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "user_role")
    search_fields = ("user_role",)

@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "user_type")
    search_fields = ("user_type",)
