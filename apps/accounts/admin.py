from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "role", "organisation", "is_verified", "date_joined"]
    list_filter = ["role", "is_verified", "is_active"]
    search_fields = ["email", "username", "organisation"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile", {"fields": ("role", "organisation", "phone", "country", "timezone", "is_verified")}),
    )
