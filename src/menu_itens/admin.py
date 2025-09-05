from django.contrib import admin
from .models import MenuItem, RoleMenuItem


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("id", "key", "label", "path", "icon", "parent", "is_active", "feature_flag")
    list_filter = ("is_active", "parent")
    search_fields = ("key", "label", "path")
    autocomplete_fields = ("parent",)


@admin.register(RoleMenuItem)
class RoleMenuItemAdmin(admin.ModelAdmin):
    list_display = ("id", "menu_item", "user_type", "user_role", "order", "is_visible")
    list_filter = ("is_visible", "user_type", "user_role")
    search_fields = ("menu_item__key", "menu_item__label", "user_type__user_type", "user_role__user_role")
    autocomplete_fields = ("menu_item", "user_type", "user_role")
