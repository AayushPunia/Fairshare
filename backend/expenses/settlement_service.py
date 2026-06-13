"""
Settlement optimization service.

Uses a greedy min-transactions algorithm to calculate the minimum
number of payments needed to settle all debts in a group.

Algorithm:
1. Get net balance for each person
2. Separate into creditors (positive balance) and debtors (negative balance)
3. Sort both lists by amount (descending)
4. Match largest debtor with largest creditor
5. Settle the minimum of abs(debt) and credit
6. Update remaining amounts
7. Repeat until all balances are zero

This produces the minimum number of transactions needed.
For Aisha's requirement: "one number per person — who pays whom, how much, done."
"""

from decimal import Decimal
from expenses.balance_service import calculate_group_balances


def suggest_settlements(group_id):
    """
    Calculate optimal settlement plan for a group.

    Returns list of settlements:
    [
        {'from': 'Rohan', 'from_id': 2, 'to': 'Aisha', 'to_id': 1, 'amount': '2300.00'},
        ...
    ]
    """
    balances = calculate_group_balances(group_id)

    # Separate into creditors and debtors
    creditors = []  # People who are owed money (positive balance)
    debtors = []    # People who owe money (negative balance)

    for user_id, data in balances.items():
        net = Decimal(data['net_balance'])
        if net > Decimal('0.01'):  # Threshold to avoid floating point dust
            creditors.append({
                'user_id': user_id,
                'name': data['user']['display_name'],
                'amount': net,
            })
        elif net < Decimal('-0.01'):
            debtors.append({
                'user_id': user_id,
                'name': data['user']['display_name'],
                'amount': abs(net),
            })

    # Sort by amount descending for greedy matching
    creditors.sort(key=lambda x: x['amount'], reverse=True)
    debtors.sort(key=lambda x: x['amount'], reverse=True)

    settlements = []

    while creditors and debtors:
        creditor = creditors[0]
        debtor = debtors[0]

        # Settle the minimum of what's owed and what's due
        settle_amount = min(creditor['amount'], debtor['amount'])

        settlements.append({
            'from': debtor['name'],
            'from_id': debtor['user_id'],
            'to': creditor['name'],
            'to_id': creditor['user_id'],
            'amount': str(settle_amount.quantize(Decimal('0.01'))),
        })

        # Update remaining balances
        creditor['amount'] -= settle_amount
        debtor['amount'] -= settle_amount

        # Remove fully settled parties
        if creditor['amount'] < Decimal('0.01'):
            creditors.pop(0)
        if debtor['amount'] < Decimal('0.01'):
            debtors.pop(0)

    return settlements
