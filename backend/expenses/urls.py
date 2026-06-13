from django.urls import path
from . import views

urlpatterns = [
    # Expenses for a group
    path('group/<int:group_id>/', views.ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('<int:pk>/', views.ExpenseDetailView.as_view(), name='expense-detail'),

    # Balances
    path('group/<int:group_id>/balances/', views.BalanceView.as_view(), name='group-balances'),

    # Settlements
    path('group/<int:group_id>/settlements/', views.SettlementListView.as_view(), name='settlement-list'),
    path('group/<int:group_id>/settlements/suggest/', views.SettlementSuggestView.as_view(), name='settlement-suggest'),
    path('settlements/', views.SettlementCreateView.as_view(), name='settlement-create'),
]
