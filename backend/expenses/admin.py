from django.contrib import admin
from .models import Expense, ExpenseSplit, Settlement


class ExpenseSplitInline(admin.TabularInline):
    model = ExpenseSplit
    extra = 0


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'paid_by', 'amount', 'currency', 'split_type', 'date', 'is_settlement')
    list_filter = ('split_type', 'currency', 'is_settlement', 'group')
    search_fields = ('description',)
    inlines = [ExpenseSplitInline]


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'amount', 'currency', 'date')
    list_filter = ('group',)
