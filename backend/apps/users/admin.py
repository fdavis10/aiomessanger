from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Profile",
            {"fields": ("avatar", "banner_image", "banner_style", "phone", "bio", "last_seen_at")},
        ),
    )
    list_display = ("username", "email", "is_staff", "last_seen_at", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
