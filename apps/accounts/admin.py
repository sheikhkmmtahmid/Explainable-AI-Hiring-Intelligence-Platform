from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "role", "organization", "is_verified", "date_joined"]
    list_filter = ["role", "is_verified", "is_active", "organization"]
    search_fields = ["email", "username", "organization__name"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile", {"fields": ("role", "organization", "phone", "country", "timezone", "is_verified")}),
    )
