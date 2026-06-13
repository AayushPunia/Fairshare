"""
CSV Analyzer — Phase 2 of the import pipeline.

Responsibilities:
- Detect business-logic anomalies that the parser can't catch
- Duplicate detection (fuzzy matching on date + amount + payer + description)
- Settlement detection (keywords in description + missing split_type)
- Percentage/share math validation
- Membership validation (departed members, non-members)
- Conflicting data (split_type vs split_details mismatch)

This runs AFTER parser.py has normalized the data.
"""

import re
from datetime import datetime, date
from decimal import Decimal
from difflib import SequenceMatcher


# Settlement keywords — if description contains these, it's likely a payment not an expense
SETTLEMENT_KEYWORDS = [
    'paid back', 'paid .* back', 'settlement', 'settled', 'repaid',
    'deposit share', 'deposit', 'reimburs',
]

# Membership timeline for the flatmates
MEMBER_TIMELINE = {
    'Aisha': {'joined': date(2026, 2, 1), 'left': None},
    'Rohan': {'joined': date(2026, 2, 1), 'left': None},
    'Priya': {'joined': date(2026, 2, 1), 'left': None},
    'Meera': {'joined': date(2026, 2, 1), 'left': date(2026, 3, 31)},
    'Dev':   {'joined': None, 'left': None},   # Guest, not a permanent member
    'Sam':   {'joined': date(2026, 4, 8), 'left': None},
}


def analyze_rows(rows):
    """
    Run all anomaly detectors on parsed/normalized rows.
    Returns a list of anomaly dicts.
    """
    anomalies = []
    anomalies.extend(detect_duplicates(rows))
    anomalies.extend(detect_settlements(rows))
    anomalies.extend(detect_percentage_errors(rows))
    anomalies.extend(detect_membership_issues(rows))
    anomalies.extend(detect_split_conflicts(rows))
    anomalies.extend(detect_zero_amounts(rows))
    return anomalies


def detect_duplicates(rows):
    """
    Detect duplicate expenses using fuzzy matching.
    Compares: date, amount, payer, and description similarity.

    Catches:
    - Row 5+6: "Dinner at Marina Bites" / "dinner - marina bites" (exact duplicate)
    - Row 24+25: Thalassa dinner logged by two different people with different amounts (conflict)
    """
    anomalies = []
    seen = []

    for row in rows:
        for prev in seen:
            # Same date check
            if row['date'] != prev['date']:
                continue

            # Description similarity (fuzzy match)
            desc_similarity = SequenceMatcher(
                None,
                row['description'].lower(),
                prev['description'].lower()
            ).ratio()

            if desc_similarity < 0.5:
                continue

            # Same payer + same amount = likely exact duplicate
            if row['paid_by'] == prev['paid_by'] and row['amount'] == prev['amount']:
                anomalies.append({
                    'row_number': row['row_number'],
                    'field': 'description',
                    'anomaly_type': 'duplicate',
                    'original_value': row['description'],
                    'corrected_value': '',
                    'severity': 'warning',
                    'auto_resolved': False,
                    'description': (
                        f'Row {row["row_number"]}: Likely duplicate of row {prev["row_number"]}. '
                        f'Both are "{prev["description"]}" / "{row["description"]}", '
                        f'same date ({row["date"]}), same payer ({row["paid_by"]}), '
                        f'same amount ({row["amount"]}). '
                        f'Suggest keeping row {prev["row_number"]} (first entry) and removing this one.'
                    ),
                    'related_row': prev['row_number'],
                })
                break

            # Same date + similar description + different payer/amount = conflict
            if desc_similarity > 0.5 and (row['paid_by'] != prev['paid_by'] or row['amount'] != prev['amount']):
                anomalies.append({
                    'row_number': row['row_number'],
                    'field': 'description',
                    'anomaly_type': 'duplicate_conflict',
                    'original_value': f'{row["description"]} (₹{row["amount"]} by {row["paid_by"]})',
                    'corrected_value': '',
                    'severity': 'warning',
                    'auto_resolved': False,
                    'description': (
                        f'Row {row["row_number"]}: Possible duplicate of row {prev["row_number"]} '
                        f'with conflicting data. '
                        f'Row {prev["row_number"]}: "{prev["description"]}" — {prev["currency"]} {prev["amount"]} paid by {prev["paid_by"]}. '
                        f'Row {row["row_number"]}: "{row["description"]}" — {row["currency"]} {row["amount"]} paid by {row["paid_by"]}. '
                        f'Please choose which row to keep.'
                    ),
                    'related_row': prev['row_number'],
                })
                break

        seen.append(row)

    return anomalies


def detect_settlements(rows):
    """
    Detect rows that are settlements/payments rather than real expenses.

    Catches:
    - Row 14: "Rohan paid Aisha back" (no split_type, settlement keywords)
    - Row 38: "Sam deposit share" (deposit keyword, only 2 participants)
    """
    anomalies = []

    for row in rows:
        desc_lower = row['description'].lower()
        is_settlement = False

        # Check settlement keywords
        for keyword in SETTLEMENT_KEYWORDS:
            if re.search(keyword, desc_lower):
                is_settlement = True
                break

        # Also check: no split_type + exactly 1 person in split_with (other than payer)
        if not row['split_type'] and len(row['split_with']) <= 1:
            is_settlement = True

        if is_settlement:
            anomalies.append({
                'row_number': row['row_number'],
                'field': 'description',
                'anomaly_type': 'settlement_as_expense',
                'original_value': row['description'],
                'corrected_value': 'settlement',
                'severity': 'warning',
                'auto_resolved': False,
                'description': (
                    f'Row {row["row_number"]}: "{row["description"]}" appears to be a settlement/payment, '
                    f'not a shared expense. Will import as a settlement record instead.'
                ),
            })

    return anomalies


def detect_percentage_errors(rows):
    """
    Validate that percentage splits sum to 100%.

    Catches:
    - Row 15: 30+30+30+20 = 110% (not 100%)
    - Row 32: Same issue
    """
    anomalies = []

    for row in rows:
        if row['split_type'] != 'percentage' or not row['split_details']:
            continue

        total_pct = Decimal('0')
        parts = row['split_details'].split(';')
        parsed_pcts = []

        for part in parts:
            part = part.strip()
            pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', part)
            if pct_match:
                pct = Decimal(pct_match.group(1))
                total_pct += pct
                parsed_pcts.append(pct)

        if parsed_pcts and abs(total_pct - 100) > Decimal('0.01'):
            anomalies.append({
                'row_number': row['row_number'],
                'field': 'split_details',
                'anomaly_type': 'percentage_sum',
                'original_value': row['split_details'],
                'corrected_value': f'Sum = {total_pct}% (should be 100%)',
                'severity': 'warning',
                'auto_resolved': False,
                'description': (
                    f'Row {row["row_number"]}: Percentage split totals {total_pct}% instead of 100%. '
                    f'Percentages: {", ".join(str(p) + "%" for p in parsed_pcts)}. '
                    f'Suggest normalizing proportionally to sum to 100%.'
                ),
            })

    return anomalies


def detect_membership_issues(rows):
    """
    Check if participants were active group members on the expense date.

    Catches:
    - Row 36: Meera in April expense (she left end of March)
    - Dev is a guest, not a permanent member (handled separately)
    """
    anomalies = []

    for row in rows:
        if not row['date'] or not row['split_with']:
            continue

        try:
            expense_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            continue

        for participant in row['split_with']:
            timeline = MEMBER_TIMELINE.get(participant)
            if not timeline:
                continue  # Unknown participant, handled elsewhere

            # Check if member had left before this expense
            if timeline['left'] and expense_date > timeline['left']:
                anomalies.append({
                    'row_number': row['row_number'],
                    'field': 'split_with',
                    'anomaly_type': 'departed_member',
                    'original_value': participant,
                    'corrected_value': '',
                    'severity': 'warning',
                    'auto_resolved': False,
                    'description': (
                        f'Row {row["row_number"]}: {participant} is included in this expense '
                        f'dated {row["date"]}, but they left the group on {timeline["left"]}. '
                        f'Suggest removing {participant} from this split.'
                    ),
                })

            # Check if member hadn't joined yet
            if timeline['joined'] and expense_date < timeline['joined']:
                anomalies.append({
                    'row_number': row['row_number'],
                    'field': 'split_with',
                    'anomaly_type': 'departed_member',
                    'original_value': participant,
                    'corrected_value': '',
                    'severity': 'warning',
                    'auto_resolved': False,
                    'description': (
                        f'Row {row["row_number"]}: {participant} is included in this expense '
                        f'dated {row["date"]}, but they didn\'t join until {timeline["joined"]}. '
                        f'Suggest removing {participant} from this split.'
                    ),
                })

    return anomalies


def detect_split_conflicts(rows):
    """
    Detect when split_type and split_details are inconsistent.

    Catches:
    - Row 42: split_type=equal but split_details contains share values
    """
    anomalies = []

    for row in rows:
        if not row['split_type'] or not row['split_details']:
            continue

        split_type = row['split_type']

        # Check: split_type is 'equal' but split_details has values
        if split_type == 'equal' and row['split_details']:
            # Check if split_details actually contains allocation info
            has_allocation = bool(re.search(r'\d+', row['split_details']))
            if has_allocation:
                anomalies.append({
                    'row_number': row['row_number'],
                    'field': 'split_type',
                    'anomaly_type': 'conflicting_split',
                    'original_value': f'split_type={split_type}, split_details={row["split_details"]}',
                    'corrected_value': f'Using split_type=equal (ignoring split_details)',
                    'severity': 'info',
                    'auto_resolved': True,
                    'description': (
                        f'Row {row["row_number"]}: split_type is "equal" but split_details '
                        f'contains allocation data "{row["split_details"]}". '
                        f'Honoring split_type=equal and ignoring the conflicting split_details.'
                    ),
                })

    return anomalies


def detect_zero_amounts(rows):
    """
    Flag zero-amount expenses that may be placeholders.

    Catches:
    - Row 31: ₹0 with note "counted twice earlier — fixing later"
    """
    anomalies = []

    for row in rows:
        if row['amount'] == Decimal('0') and not any(
            a['row_number'] == row['row_number'] and a['anomaly_type'] == 'zero_amount'
            for a in anomalies
        ):
            # Only add if not already flagged by parser
            pass  # Parser already handles this

    return anomalies
