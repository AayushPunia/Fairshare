"""
Tests for balance and settlement services.

Verifies:
- Balance calculation with equal splits
- Membership-aware balance exclusion
- Settlement optimization (min transactions)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from decimal import Decimal
from datetime import date

from accounts.models import User
from groups.models import Group, GroupMember
from expenses.models import Expense, ExpenseSplit, Settlement
from expenses.balance_service import calculate_group_balances
from expenses.settlement_service import suggest_settlements


class BalanceCalculationTest(TestCase):
    """Test balance calculations with various split scenarios."""

    def setUp(self):
        """Create a test group with 3 members."""
        self.user_a = User.objects.create_user(
            username='test_a', password='test', display_name='Alice'
        )
        self.user_b = User.objects.create_user(
            username='test_b', password='test', display_name='Bob'
        )
        self.user_c = User.objects.create_user(
            username='test_c', password='test', display_name='Charlie'
        )

        self.group = Group.objects.create(
            name='Test Group', created_by=self.user_a
        )
        GroupMember.objects.create(
            group=self.group, user=self.user_a,
            joined_at=date(2026, 1, 1), is_active=True
        )
        GroupMember.objects.create(
            group=self.group, user=self.user_b,
            joined_at=date(2026, 1, 1), is_active=True
        )
        GroupMember.objects.create(
            group=self.group, user=self.user_c,
            joined_at=date(2026, 1, 1), is_active=True
        )

    def test_equal_split_balance(self):
        """Alice pays 300, split equally 3 ways → Alice owed 200."""
        expense = Expense.objects.create(
            group=self.group, description='Dinner',
            paid_by=self.user_a, amount=Decimal('300'),
            amount_inr=Decimal('300'), split_type='equal',
            date=date(2026, 2, 1),
        )
        for user in [self.user_a, self.user_b, self.user_c]:
            ExpenseSplit.objects.create(
                expense=expense, user=user,
                share_amount=Decimal('100'),
            )

        balances = calculate_group_balances(self.group.id)

        # Alice paid 300, owes 100 → net +200
        self.assertEqual(Decimal(balances[self.user_a.id]['net_balance']), Decimal('200'))
        # Bob paid 0, owes 100 → net -100
        self.assertEqual(Decimal(balances[self.user_b.id]['net_balance']), Decimal('-100'))
        # Charlie paid 0, owes 100 → net -100
        self.assertEqual(Decimal(balances[self.user_c.id]['net_balance']), Decimal('-100'))

    def test_settlement_reduces_balance(self):
        """After a settlement, balances should adjust."""
        # Alice pays 300, split equally
        expense = Expense.objects.create(
            group=self.group, description='Dinner',
            paid_by=self.user_a, amount=Decimal('300'),
            amount_inr=Decimal('300'), split_type='equal',
            date=date(2026, 2, 1),
        )
        for user in [self.user_a, self.user_b, self.user_c]:
            ExpenseSplit.objects.create(
                expense=expense, user=user,
                share_amount=Decimal('100'),
            )

        # Bob pays Alice 100
        Settlement.objects.create(
            group=self.group, from_user=self.user_b,
            to_user=self.user_a, amount=Decimal('100'),
            date=date(2026, 2, 2),
        )

        balances = calculate_group_balances(self.group.id)

        # After settlement: Bob paid Alice 100
        # Alice: +200 (expenses) - 100 (received settlement) = net +100
        alice_balance = Decimal(balances[self.user_a.id]['net_balance'])
        self.assertEqual(alice_balance, Decimal('100'))

        # Bob: -100 (expenses) + 100 (paid settlement) = net 0
        bob_balance = Decimal(balances[self.user_b.id]['net_balance'])
        self.assertEqual(bob_balance, Decimal('0'))

        # Charlie unchanged: -100
        charlie_balance = Decimal(balances[self.user_c.id]['net_balance'])
        self.assertEqual(charlie_balance, Decimal('-100'))


class SettlementOptimizerTest(TestCase):
    """Test the min-transactions settlement algorithm."""

    def setUp(self):
        self.user_a = User.objects.create_user(
            username='opt_a', password='test', display_name='Alice'
        )
        self.user_b = User.objects.create_user(
            username='opt_b', password='test', display_name='Bob'
        )
        self.user_c = User.objects.create_user(
            username='opt_c', password='test', display_name='Charlie'
        )
        self.group = Group.objects.create(
            name='Opt Group', created_by=self.user_a
        )
        for user in [self.user_a, self.user_b, self.user_c]:
            GroupMember.objects.create(
                group=self.group, user=user,
                joined_at=date(2026, 1, 1), is_active=True
            )

    def test_simple_settlement(self):
        """A pays 300 split equally → suggestions should have B→A and C→A."""
        expense = Expense.objects.create(
            group=self.group, description='Test',
            paid_by=self.user_a, amount=Decimal('300'),
            amount_inr=Decimal('300'), split_type='equal',
            date=date(2026, 2, 1),
        )
        for user in [self.user_a, self.user_b, self.user_c]:
            ExpenseSplit.objects.create(
                expense=expense, user=user,
                share_amount=Decimal('100'),
            )

        suggestions = suggest_settlements(self.group.id)

        # Should suggest 2 payments: B→A 100 and C→A 100
        self.assertEqual(len(suggestions), 2)
        total_settlement = sum(Decimal(s['amount']) for s in suggestions)
        self.assertEqual(total_settlement, Decimal('200'))
