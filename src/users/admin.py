# src/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from src.users.models import Profile, UserType, UserRole
from src.forms.models import FormSubmission


@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "user_type")
    search_fields = ("user_type",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("id", "user_role")
    search_fields = ("user_role",)


class ProfileInline(admin.StackedInline):
    """
    Edita o Profile direto na página do User.
    """
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = (
        "first_name",
        "middle_name",
        "last_name",
        "email",
        "phone_number",
        "phone_number_type",
        "date_of_birth",
        "signed_date",
        "user_type",
        "user_role",
        "company",                # autocomplete OK
        "insuranceCoverage",
        "coverageType",
        "image",
        "formType",  # 🌟 Adicione esta linha

    )
    autocomplete_fields = ("user_type", "user_role", "company")


class UserAdmin(BaseUserAdmin):
    """
    Adiciona o Profile ao admin de User.
    """
    inlines = (ProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "profile__user_role",
        "profile__user_type",
        "profile__company",
        "profile__insuranceCoverage",
        "profile__coverageType",
        "profile__formType",  # 🌟 Adicione esta linha

    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "profile__first_name",
        "profile__last_name",
        "profile__email",
        "profile__phone_number",
        "profile__insuranceCoverage",
        "profile__coverageType",
        "profile__formType",  # 🌟 Adicione esta linha

    )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


# Substitui o admin padrão de User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)



@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "first_name",
        "last_name",
        "phone_number",
        "email",
        "user_type",
        "user_role",
        "company",
        "insuranceCoverage",
        "coverageType",
        "formType", # 🌟 Adicione esta linha e remova o método 'get_form_type'
    )
    list_filter = ("user_type", "user_role", "company", "formType") # 🌟 Adicione esta linha
    search_fields = (
        "user__username",
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "insuranceCoverage",
        "coverageType",
        "formType",  # 🌟 Adicione esta linha

    )
    autocomplete_fields = ("user_type", "user_role", "company")


