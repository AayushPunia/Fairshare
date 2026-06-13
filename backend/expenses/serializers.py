from rest_framework import serializers
from .models import Expense, ExpenseSplit, Settlement
from accounts.serializers import UserSerializer


class ExpenseSplitSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ExpenseSplit
        fields = ['id', 'user', 'user_id', 'share_amount', 'share_percentage', 'share_units']
        read_only_fields = ['id']


class ExpenseSerializer(serializers.ModelSerializer):
    splits = ExpenseSplitSerializer(many=True, read_only=True)
    paid_by = UserSerializer(read_only=True)
    paid_by_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Expense
        fields = [
            'id', 'group', 'description', 'paid_by', 'paid_by_id',
            'amount', 'currency', 'amount_inr', 'exchange_rate',
            'split_type', 'date', 'notes', 'is_settlement',
            'splits', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'amount_inr', 'created_at', 'updated_at']


class ExpenseCreateSerializer(serializers.Serializer):
    """
    Handles creating an expense with splits.
    Accepts split details in a flexible format to support all split types.
    """
    group_id = serializers.IntegerField()
    description = serializers.CharField(max_length=500)
    paid_by_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='INR')
    split_type = serializers.ChoiceField(choices=['equal', 'unequal', 'percentage', 'share'])
    date = serializers.DateField()
    notes = serializers.CharField(required=False, default='', allow_blank=True)
    is_settlement = serializers.BooleanField(default=False)

    # Split participants: list of {user_id, amount/percentage/shares}
    participants = serializers.ListField(child=serializers.DictField(), required=True)

    def validate(self, data):
        """Validate split math based on split_type."""
        from django.conf import settings
        from decimal import Decimal

        participants = data['participants']
        amount = data['amount']
        split_type = data['split_type']
        currency = data.get('currency', 'INR')

        # Convert to INR
        if currency == 'USD':
            rate = Decimal(str(settings.DEFAULT_USD_TO_INR))
            data['amount_inr'] = amount * rate
            data['exchange_rate'] = rate
        else:
            data['amount_inr'] = amount
            data['exchange_rate'] = Decimal('1.0')

        if split_type == 'percentage':
            total_pct = sum(Decimal(str(p.get('percentage', 0))) for p in participants)
            if abs(total_pct - 100) > Decimal('0.01'):
                raise serializers.ValidationError(
                    f'Percentages must sum to 100%, got {total_pct}%'
                )

        return data


class SettlementSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    from_user_id = serializers.IntegerField(write_only=True)
    to_user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Settlement
        fields = [
            'id', 'group', 'from_user', 'from_user_id',
            'to_user', 'to_user_id', 'amount', 'currency',
            'date', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SettlementCreateSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='INR')
    date = serializers.DateField()
    notes = serializers.CharField(required=False, default='', allow_blank=True)
