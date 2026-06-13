from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'display_name', 'email', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra', {'fields': ('display_name',)}),
    )
