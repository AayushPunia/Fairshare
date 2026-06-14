from django.contrib import admin
from .models import Group, GroupMember


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'default_currency', 'created_by', 'created_at']
    search_fields = ['name']
    list_filter = ['default_currency']


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'joined_at', 'left_at', 'is_active']
    list_filter = ['is_active', 'group']
    search_fields = ['user__display_name', 'group__name']
