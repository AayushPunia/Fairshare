from django.contrib import admin
from .models import Expense, ExpenseSplit, Settlement


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'paid_by', 'amount', 'currency', 'split_type', 'date', 'is_settlement']
    list_filter = ['currency', 'split_type', 'is_settlement', 'group']
    search_fields = ['description', 'paid_by__display_name']
    date_hierarchy = 'date'


@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
    list_display = ['expense', 'user', 'share_amount', 'share_percentage', 'share_units']
    list_filter = ['expense__group']
    search_fields = ['user__display_name', 'expense__description']


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'amount', 'currency', 'date']
    list_filter = ['currency', 'group']
    search_fields = ['from_user__display_name', 'to_user__display_name']
    date_hierarchy = 'date'
