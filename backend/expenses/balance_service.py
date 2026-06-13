"""
Balance calculation service.

Computes who owes whom in a group by processing all expenses and settlements.
Membership-aware: only charges members for expenses dated during their active period.

Balance logic:
  For each expense:
    1. Convert to INR using stored exchange_rate
    2. Calculate each participant's share based on split_type
    3. Payer gets credited the full amount (they fronted the money)
    4. Each participant gets debited their share (they owe that portion)
    5. Skip participants who weren't active members on the expense date

  For each settlement:
    The payer (from_user) gets debited, receiver (to_user) gets credited.

  Net balance = total_credits - total_debits
  Positive → others owe this person
  Negative → this person owes others
"""

from decimal import Decimal
from collections import defaultdict
from expenses.models import Expense, ExpenseSplit, Settlement
from groups.models import Group, GroupMember


def calculate_group_balances(group_id):
    """
    Calculate net balances for all members of a group.

    Returns:
    {
        user_id: {
            'user': { 'id': ..., 'display_name': ... },
            'net_balance': Decimal,
            'total_paid': Decimal,
            'total_owed': Decimal,
            'expenses_paid': [...],     # Expenses this user paid for
            'expenses_shared': [...],   # Expenses this user owes a share of
            'settlements_made': [...],
            'settlements_received': [...],
        }
    }
    """
    group = Group.objects.get(id=group_id)
    members = GroupMember.objects.filter(group=group).select_related('user')

    # Build membership date ranges for validation
    member_dates = {}
    for m in members:
        member_dates[m.user_id] = {
            'joined_at': m.joined_at,
            'left_at': m.left_at,
            'user': {
                'id': m.user_id,
                'display_name': m.user.display_name,
                'username': m.user.username,
            }
        }

    # Initialize balances
    balances = {}
    for user_id, info in member_dates.items():
        balances[user_id] = {
            'user': info['user'],
            'net_balance': Decimal('0'),
            'total_paid': Decimal('0'),
            'total_owed': Decimal('0'),
            'expenses_paid': [],
            'expenses_shared': [],
            'settlements_made': [],
            'settlements_received': [],
        }

    # Process all non-settlement expenses
    expenses = Expense.objects.filter(
        group=group, is_settlement=False
    ).prefetch_related('splits__user').select_related('paid_by')

    for expense in expenses:
        payer_id = expense.paid_by_id
        amount_inr = expense.amount_inr

        # Credit the payer (they fronted the money)
        if payer_id in balances:
            balances[payer_id]['total_paid'] += amount_inr
            balances[payer_id]['net_balance'] += amount_inr
            balances[payer_id]['expenses_paid'].append({
                'id': expense.id,
                'description': expense.description,
                'amount': str(expense.amount),
                'currency': expense.currency,
                'amount_inr': str(amount_inr),
                'date': str(expense.date),
            })

        # Debit each participant their share
        for split in expense.splits.all():
            user_id = split.user_id
            if user_id in balances:
                # Check membership dates — only charge if active on expense date
                m_info = member_dates.get(user_id)
                if m_info:
                    joined = m_info['joined_at']
                    left = m_info['left_at']
                    if expense.date < joined:
                        continue  # Sam's case: not yet joined
                    if left and expense.date > left:
                        continue  # Meera's case: already left

                balances[user_id]['total_owed'] += split.share_amount
                balances[user_id]['net_balance'] -= split.share_amount
                balances[user_id]['expenses_shared'].append({
                    'id': expense.id,
                    'description': expense.description,
                    'share_amount': str(split.share_amount),
                    'date': str(expense.date),
                    'paid_by': expense.paid_by.display_name,
                })

    # Process settlements
    settlements = Settlement.objects.filter(group=group).select_related(
        'from_user', 'to_user'
    )
    for settlement in settlements:
        from_id = settlement.from_user_id
        to_id = settlement.to_user_id
        amount = settlement.amount

        if from_id in balances:
            balances[from_id]['net_balance'] -= amount
            balances[from_id]['settlements_made'].append({
                'id': settlement.id,
                'to': settlement.to_user.display_name,
                'amount': str(amount),
                'date': str(settlement.date),
            })

        if to_id in balances:
            balances[to_id]['net_balance'] += amount
            balances[to_id]['settlements_received'].append({
                'id': settlement.id,
                'from': settlement.from_user.display_name,
                'amount': str(amount),
                'date': str(settlement.date),
            })

    # Convert Decimal to string for JSON serialization
    for user_id, b in balances.items():
        b['net_balance'] = str(b['net_balance'])
        b['total_paid'] = str(b['total_paid'])
        b['total_owed'] = str(b['total_owed'])

    return balances
