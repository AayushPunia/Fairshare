"""
CSV Importer — Phase 3 of the import pipeline.

Responsibilities:
- After user has reviewed and resolved anomalies, commit clean data to the database
- Create Expense + ExpenseSplit records for normal expenses
- Create Settlement records for detected settlements
- Handle currency conversion (USD → INR)
- Respect split types and calculate shares
- Update ImportSession status and stats
"""

import re
from decimal import Decimal
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from accounts.models import User
from groups.models import Group, GroupMember
from expenses.models import Expense, ExpenseSplit, Settlement
from importer.models import ImportSession


def commit_import(session_id, resolved_rows):
    """
    Commit resolved import data to the database.

    Args:
        session_id: ImportSession ID
        resolved_rows: List of row dicts with user resolutions applied.
                       Each row has 'action': 'import' | 'skip' | 'settlement'

    Returns:
        Stats dict with counts of imported, skipped, and settlement records.
    """
    session = ImportSession.objects.get(id=session_id)
    group = session.group

    stats = {'imported': 0, 'skipped': 0, 'settlements': 0, 'errors': []}

    # Build user lookup by display_name
    users = {u.display_name: u for u in User.objects.all()}
    # Also map by lowercase for case-insensitive lookup
    users_lower = {name.lower(): u for name, u in users.items()}

    for row in resolved_rows:
        action = row.get('action', 'import')

        if action == 'skip':
            stats['skipped'] += 1
            continue

        try:
            if action == 'settlement':
                _create_settlement(row, group, users_lower, session)
                stats['settlements'] += 1
            else:
                _create_expense(row, group, users_lower, session)
                stats['imported'] += 1
        except Exception as e:
            stats['errors'].append({
                'row': row.get('row_number', '?'),
                'error': str(e),
            })

    # Update session
    session.status = 'completed'
    session.imported_rows = stats['imported']
    session.skipped_rows = stats['skipped']
    session.completed_at = timezone.now()
    session.save()

    return stats


def _find_user(name, users_lower):
    """Look up a user by display name (case-insensitive)."""
    user = users_lower.get(name.lower())
    if not user:
        # Try creating a guest user for unknown participants
        user, created = User.objects.get_or_create(
            username=name.lower().replace(' ', '_').replace("'", ''),
            defaults={
                'display_name': name,
                'first_name': name.split()[0] if name else name,
            }
        )
        if created:
            user.set_unusable_password()
            user.save()
            users_lower[name.lower()] = user
    return user


def _create_settlement(row, group, users_lower, session):
    """Create a Settlement record from a CSV row detected as a settlement."""
    payer = _find_user(row['paid_by'], users_lower)

    # The recipient is the person in split_with (or first participant)
    recipients = row.get('split_with', [])
    if not recipients:
        raise ValueError(f'Settlement row {row["row_number"]} has no recipient')

    recipient_name = recipients[0]
    recipient = _find_user(recipient_name, users_lower)

    amount = abs(row['amount'])
    currency = row.get('currency', 'INR')

    Settlement.objects.create(
        group=group,
        from_user=payer,
        to_user=recipient,
        amount=amount,
        currency=currency,
        date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
        notes=row.get('notes', f'Imported from CSV row {row["row_number"]}'),
    )


def _create_expense(row, group, users_lower, session):
    """Create an Expense with ExpenseSplits from a CSV row."""
    payer = _find_user(row['paid_by'], users_lower)

    amount = row['amount']
    currency = row.get('currency', 'INR')

    # Currency conversion
    if currency == 'USD':
        exchange_rate = Decimal(str(settings.DEFAULT_USD_TO_INR))
        amount_inr = amount * exchange_rate
    else:
        exchange_rate = Decimal('1.0')
        amount_inr = amount

    # Round to 2 decimal places
    amount_inr = amount_inr.quantize(Decimal('0.01'))

    split_type = row.get('split_type', 'equal') or 'equal'
    participants = row.get('split_with', [])

    expense = Expense.objects.create(
        group=group,
        description=row['description'],
        paid_by=payer,
        amount=amount,
        currency=currency,
        amount_inr=amount_inr,
        exchange_rate=exchange_rate,
        split_type=split_type,
        date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
        notes=row.get('notes', ''),
        is_settlement=False,
        import_session=session,
    )

    # Create splits based on type
    if split_type == 'equal':
        _create_equal_splits(expense, participants, amount_inr, users_lower)
    elif split_type == 'unequal':
        _create_unequal_splits(expense, row, participants, amount_inr, currency, exchange_rate, users_lower)
    elif split_type == 'percentage':
        _create_percentage_splits(expense, row, participants, amount_inr, users_lower)
    elif split_type == 'share':
        _create_share_splits(expense, row, participants, amount_inr, users_lower)


def _create_equal_splits(expense, participants, amount_inr, users_lower):
    """Split equally among all participants."""
    if not participants:
        return

    share = (amount_inr / len(participants)).quantize(Decimal('0.01'))

    for name in participants:
        user = _find_user(name, users_lower)
        ExpenseSplit.objects.create(
            expense=expense,
            user=user,
            share_amount=share,
        )


def _create_unequal_splits(expense, row, participants, amount_inr, currency, exchange_rate, users_lower):
    """Split by explicit unequal amounts from split_details."""
    details = _parse_split_details(row.get('split_details', ''))

    for name in participants:
        user = _find_user(name, users_lower)
        raw_amount = details.get(name, Decimal('0'))

        # Convert if USD
        if currency == 'USD':
            share_inr = (raw_amount * exchange_rate).quantize(Decimal('0.01'))
        else:
            share_inr = raw_amount

        ExpenseSplit.objects.create(
            expense=expense,
            user=user,
            share_amount=share_inr,
        )


def _create_percentage_splits(expense, row, participants, amount_inr, users_lower):
    """Split by percentages from split_details."""
    details = _parse_split_details(row.get('split_details', ''), value_type='percentage')

    # If percentages don't sum to 100%, normalize them
    total_pct = sum(details.values())
    if total_pct > 0 and abs(total_pct - 100) > Decimal('0.01'):
        # Normalize proportionally
        for name in details:
            details[name] = (details[name] * 100 / total_pct).quantize(Decimal('0.01'))

    for name in participants:
        user = _find_user(name, users_lower)
        pct = details.get(name, Decimal('0'))
        share = (amount_inr * pct / 100).quantize(Decimal('0.01'))

        ExpenseSplit.objects.create(
            expense=expense,
            user=user,
            share_amount=share,
            share_percentage=pct,
        )


def _create_share_splits(expense, row, participants, amount_inr, users_lower):
    """Split by share units from split_details."""
    details = _parse_split_details(row.get('split_details', ''), value_type='units')

    total_units = sum(details.values())
    if total_units == 0:
        total_units = len(participants)
        details = {name: Decimal('1') for name in participants}

    for name in participants:
        user = _find_user(name, users_lower)
        units = details.get(name, Decimal('1'))
        share = (amount_inr * units / total_units).quantize(Decimal('0.01'))

        ExpenseSplit.objects.create(
            expense=expense,
            user=user,
            share_amount=share,
            share_units=int(units),
        )


def _parse_split_details(details_str, value_type='amount'):
    """
    Parse split_details string like "Rohan 700; Priya 400; Meera 400"
    or "Aisha 30%; Rohan 30%; Priya 30%; Meera 20%"
    or "Aisha 1; Rohan 2; Priya 1; Dev 2"

    Returns: {name: Decimal(value)}
    """
    result = {}
    if not details_str:
        return result

    parts = details_str.split(';')
    for part in parts:
        part = part.strip()
        if not part:
            continue

        if value_type == 'percentage':
            match = re.match(r'(.+?)\s+(\d+(?:\.\d+)?)\s*%', part)
        else:
            match = re.match(r'(.+?)\s+(\d+(?:\.\d+)?)', part)

        if match:
            name = match.group(1).strip()
            value = Decimal(match.group(2))
            result[name] = value

    return result
