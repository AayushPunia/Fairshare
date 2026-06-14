from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'display_name', 'email', 'is_active']
    search_fields = ['username', 'display_name', 'email']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('FairShare', {'fields': ('display_name',)}),
    )
