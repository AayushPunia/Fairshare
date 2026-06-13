from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal
from django.conf import settings

from .models import Expense, ExpenseSplit, Settlement
from .serializers import (
    ExpenseSerializer, ExpenseCreateSerializer,
    SettlementSerializer, SettlementCreateSerializer,
)
from .balance_service import calculate_group_balances
from .settlement_service import suggest_settlements
from accounts.models import User
from groups.models import Group


class ExpenseListCreateView(APIView):
    """
    GET: List expenses for a group.
    POST: Create a new expense with splits.
    """
    def get(self, request, group_id):
        expenses = Expense.objects.filter(
            group_id=group_id
        ).select_related('paid_by').prefetch_related('splits__user')
        serializer = ExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    def post(self, request, group_id):
        data = request.data.copy()
        data['group_id'] = group_id
        serializer = ExpenseCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        vd = serializer.validated_data
        group = Group.objects.get(id=group_id)
        paid_by = User.objects.get(id=vd['paid_by_id'])

        # Create the expense
        expense = Expense.objects.create(
            group=group,
            description=vd['description'],
            paid_by=paid_by,
            amount=vd['amount'],
            currency=vd.get('currency', 'INR'),
            amount_inr=vd['amount_inr'],
            exchange_rate=vd['exchange_rate'],
            split_type=vd['split_type'],
            date=vd['date'],
            notes=vd.get('notes', ''),
            is_settlement=vd.get('is_settlement', False),
        )

        # Create splits based on split_type
        participants = vd['participants']
        amount_inr = vd['amount_inr']
        split_type = vd['split_type']

        if split_type == 'equal':
            share = (amount_inr / len(participants)).quantize(Decimal('0.01'))
            for p in participants:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=p['user_id'],
                    share_amount=share,
                )

        elif split_type == 'unequal':
            for p in participants:
                p_amount = Decimal(str(p['amount']))
                # Convert if needed
                if vd.get('currency', 'INR') == 'USD':
                    p_amount_inr = p_amount * vd['exchange_rate']
                else:
                    p_amount_inr = p_amount
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=p['user_id'],
                    share_amount=p_amount_inr.quantize(Decimal('0.01')),
                )

        elif split_type == 'percentage':
            for p in participants:
                pct = Decimal(str(p['percentage']))
                share = (amount_inr * pct / 100).quantize(Decimal('0.01'))
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=p['user_id'],
                    share_amount=share,
                    share_percentage=pct,
                )

        elif split_type == 'share':
            total_units = sum(int(p.get('shares', 1)) for p in participants)
            for p in participants:
                units = int(p.get('shares', 1))
                share = (amount_inr * units / total_units).quantize(Decimal('0.01'))
                ExpenseSplit.objects.create(
                    expense=expense,
                    user_id=p['user_id'],
                    share_amount=share,
                    share_units=units,
                )

        # Reload with relations
        expense = Expense.objects.prefetch_related(
            'splits__user'
        ).select_related('paid_by').get(id=expense.id)
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Expense detail with all splits (Rohan's drill-down requirement).
    PUT/DELETE: Update or delete an expense.
    """
    serializer_class = ExpenseSerializer
    queryset = Expense.objects.all().prefetch_related('splits__user').select_related('paid_by')


class BalanceView(APIView):
    """
    GET: Calculate and return group balances with full expense drill-down.
    Rohan's requirement: "If the app says I owe ₹2,300, I want to see exactly
    which expenses make that up."
    """
    def get(self, request, group_id):
        balances = calculate_group_balances(group_id)
        return Response(balances)


class SettlementSuggestView(APIView):
    """
    GET: Get optimized settlement suggestions.
    Aisha's requirement: "one number per person — who pays whom, how much, done."
    """
    def get(self, request, group_id):
        settlements = suggest_settlements(group_id)
        return Response(settlements)


class SettlementCreateView(APIView):
    """POST: Record a settlement/payment between two users."""

    def post(self, request):
        serializer = SettlementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        settlement = Settlement.objects.create(
            group_id=vd['group_id'],
            from_user_id=vd['from_user_id'],
            to_user_id=vd['to_user_id'],
            amount=vd['amount'],
            currency=vd.get('currency', 'INR'),
            date=vd['date'],
            notes=vd.get('notes', ''),
        )
        return Response(
            SettlementSerializer(settlement).data,
            status=status.HTTP_201_CREATED,
        )


class SettlementListView(APIView):
    """GET: List all settlements for a group."""

    def get(self, request, group_id):
        settlements = Settlement.objects.filter(
            group_id=group_id
        ).select_related('from_user', 'to_user')
        serializer = SettlementSerializer(settlements, many=True)
        return Response(serializer.data)
