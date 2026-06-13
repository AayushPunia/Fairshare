"""
CSV Parser — Phase 1 of the import pipeline.

Responsibilities:
- Parse CSV file using Python's csv module
- Normalize field values (strip whitespace, fix amounts, normalize names)
- Convert dates to consistent YYYY-MM-DD format
- Return a list of normalized row dicts + a list of auto-fix anomalies

This phase does NOT validate business logic (that's Phase 2: analyzer.py).
It only handles format-level issues.
"""

import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


# Known flatmates for name normalization
KNOWN_NAMES = {
    'aisha': 'Aisha',
    'rohan': 'Rohan',
    'priya': 'Priya',
    'meera': 'Meera',
    'dev': 'Dev',
    'sam': 'Sam',
    'priya s': 'Priya',  # Name variant mapping
}


def parse_csv_file(file_content):
    """
    Parse raw CSV content and normalize each row.

    Args:
        file_content: String content of the CSV file.

    Returns:
        (rows, anomalies) where:
        - rows: list of normalized dicts
        - anomalies: list of auto-fix anomaly dicts
    """
    reader = csv.DictReader(io.StringIO(file_content))
    rows = []
    anomalies = []

    for i, raw_row in enumerate(reader, start=2):  # Row 1 is header, data starts at 2
        if not any(raw_row.values()):
            continue  # Skip empty rows

        row, row_anomalies = normalize_row(raw_row, i)
        rows.append(row)
        anomalies.extend(row_anomalies)

    return rows, anomalies


def normalize_row(raw_row, row_number):
    """
    Normalize a single CSV row. Returns (normalized_row, anomalies).
    """
    anomalies = []
    row = {
        'row_number': row_number,
        'original': dict(raw_row),
    }

    # --- Date normalization ---
    raw_date = (raw_row.get('date') or '').strip()
    parsed_date, date_anomaly = normalize_date(raw_date, row_number)
    row['date'] = parsed_date
    if date_anomaly:
        anomalies.append(date_anomaly)

    # --- Description ---
    row['description'] = (raw_row.get('description') or '').strip()

    # --- Paid by (name normalization) ---
    raw_payer = (raw_row.get('paid_by') or '').strip()
    payer, payer_anomalies = normalize_name(raw_payer, row_number, 'paid_by')
    row['paid_by'] = payer
    anomalies.extend(payer_anomalies)

    # --- Amount normalization ---
    raw_amount = (raw_row.get('amount') or '').strip()
    amount, amount_anomalies = normalize_amount(raw_amount, row_number)
    row['amount'] = amount
    anomalies.extend(amount_anomalies)

    # --- Currency ---
    raw_currency = (raw_row.get('currency') or '').strip().upper()
    if not raw_currency:
        raw_currency = 'INR'
        anomalies.append({
            'row_number': row_number,
            'field': 'currency',
            'anomaly_type': 'missing_currency',
            'original_value': '',
            'corrected_value': 'INR',
            'severity': 'warning',
            'auto_resolved': True,
            'description': f'Row {row_number}: Missing currency. Defaulted to INR.',
        })
    row['currency'] = raw_currency

    # --- Split type ---
    row['split_type'] = (raw_row.get('split_type') or '').strip().lower()

    # --- Split with (participant names) ---
    raw_split_with = (raw_row.get('split_with') or '').strip()
    participants = []
    participant_anomalies = []
    if raw_split_with:
        for name in raw_split_with.split(';'):
            name = name.strip()
            if name:
                normalized, name_anoms = normalize_name(name, row_number, 'split_with')
                participants.append(normalized)
                participant_anomalies.extend(name_anoms)
    row['split_with'] = participants
    anomalies.extend(participant_anomalies)

    # --- Split details ---
    row['split_details'] = (raw_row.get('split_details') or '').strip()

    # --- Notes ---
    row['notes'] = (raw_row.get('notes') or '').strip()

    return row, anomalies


def normalize_date(raw_date, row_number):
    """
    Parse various date formats and normalize to YYYY-MM-DD.
    Handles: DD-MM-YYYY, Mon-DD, ambiguous DD-MM vs MM-DD.
    """
    if not raw_date:
        return None, {
            'row_number': row_number,
            'field': 'date',
            'anomaly_type': 'format_date',
            'original_value': '',
            'corrected_value': '',
            'severity': 'critical',
            'auto_resolved': False,
            'description': f'Row {row_number}: Missing date.',
        }

    # Try standard DD-MM-YYYY format
    for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d']:
        try:
            dt = datetime.strptime(raw_date, fmt)
            return dt.strftime('%Y-%m-%d'), None
        except ValueError:
            continue

    # Try Mon-DD format (e.g., "Mar-14")
    month_match = re.match(r'^([A-Za-z]{3})-(\d{1,2})$', raw_date)
    if month_match:
        try:
            month_str = month_match.group(1)
            day = int(month_match.group(2))
            # Assume 2026 based on context
            dt = datetime.strptime(f'{day}-{month_str}-2026', '%d-%b-%Y')
            corrected = dt.strftime('%Y-%m-%d')
            return corrected, {
                'row_number': row_number,
                'field': 'date',
                'anomaly_type': 'format_date',
                'original_value': raw_date,
                'corrected_value': corrected,
                'severity': 'warning',
                'auto_resolved': True,
                'description': f'Row {row_number}: Non-standard date format "{raw_date}". Parsed as {corrected}.',
            }
        except ValueError:
            pass

    # Check for ambiguous DD-MM vs MM-DD (e.g., 04-05-2026)
    parts_match = re.match(r'^(\d{2})-(\d{2})-(\d{4})$', raw_date)
    if parts_match:
        d, m, y = int(parts_match.group(1)), int(parts_match.group(2)), int(parts_match.group(3))
        # If both d and m could be valid months, flag as ambiguous
        if d <= 12 and m <= 12 and d != m:
            # Default to DD-MM-YYYY (CSV's dominant format)
            try:
                dt = datetime(y, m, d)
                corrected = dt.strftime('%Y-%m-%d')
                return corrected, {
                    'row_number': row_number,
                    'field': 'date',
                    'anomaly_type': 'date_ambiguous',
                    'original_value': raw_date,
                    'corrected_value': corrected,
                    'severity': 'critical',
                    'auto_resolved': False,
                    'description': (
                        f'Row {row_number}: Ambiguous date "{raw_date}". '
                        f'Could be {d:02d}/{m:02d}/{y} (DD-MM) or {m:02d}/{d:02d}/{y} (MM-DD). '
                        f'Defaulted to DD-MM format → {corrected}. Please verify.'
                    ),
                }
            except ValueError:
                pass

    return raw_date, {
        'row_number': row_number,
        'field': 'date',
        'anomaly_type': 'format_date',
        'original_value': raw_date,
        'corrected_value': '',
        'severity': 'critical',
        'auto_resolved': False,
        'description': f'Row {row_number}: Unable to parse date "{raw_date}".',
    }


def normalize_amount(raw_amount, row_number):
    """
    Parse amount, stripping commas and handling edge cases.
    """
    anomalies = []
    if not raw_amount:
        return Decimal('0'), [{
            'row_number': row_number,
            'field': 'amount',
            'anomaly_type': 'format_amount',
            'original_value': '',
            'corrected_value': '0',
            'severity': 'error',
            'auto_resolved': False,
            'description': f'Row {row_number}: Missing amount.',
        }]

    # Strip commas (e.g., "1,200" → "1200")
    cleaned = raw_amount.replace(',', '')
    if cleaned != raw_amount:
        anomalies.append({
            'row_number': row_number,
            'field': 'amount',
            'anomaly_type': 'format_amount',
            'original_value': raw_amount,
            'corrected_value': cleaned,
            'severity': 'info',
            'auto_resolved': True,
            'description': f'Row {row_number}: Stripped comma from amount "{raw_amount}" → "{cleaned}".',
        })

    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        return Decimal('0'), anomalies + [{
            'row_number': row_number,
            'field': 'amount',
            'anomaly_type': 'format_amount',
            'original_value': raw_amount,
            'corrected_value': '0',
            'severity': 'error',
            'auto_resolved': False,
            'description': f'Row {row_number}: Cannot parse amount "{raw_amount}".',
        }]

    # Check for negative amounts (refunds)
    if amount < 0:
        anomalies.append({
            'row_number': row_number,
            'field': 'amount',
            'anomaly_type': 'negative_amount',
            'original_value': str(amount),
            'corrected_value': str(amount),
            'severity': 'info',
            'auto_resolved': True,
            'description': f'Row {row_number}: Negative amount {amount}. Treating as refund/credit.',
        })

    # Check for zero amounts
    if amount == 0:
        anomalies.append({
            'row_number': row_number,
            'field': 'amount',
            'anomaly_type': 'zero_amount',
            'original_value': '0',
            'corrected_value': '0',
            'severity': 'warning',
            'auto_resolved': False,
            'description': f'Row {row_number}: Zero amount. This expense has no value — suggest skipping.',
        })

    # Check for excessive decimal precision
    if '.' in cleaned:
        decimal_part = cleaned.split('.')[1]
        if len(decimal_part) > 2:
            rounded = amount.quantize(Decimal('0.01'))
            anomalies.append({
                'row_number': row_number,
                'field': 'amount',
                'anomaly_type': 'decimal_precision',
                'original_value': str(amount),
                'corrected_value': str(rounded),
                'severity': 'info',
                'auto_resolved': True,
                'description': f'Row {row_number}: Amount {amount} has excessive decimals. Rounded to {rounded}.',
            })
            amount = rounded

    return amount, anomalies


def normalize_name(raw_name, row_number, field):
    """
    Normalize a person's name to match known flatmates.
    """
    anomalies = []
    if not raw_name:
        if field == 'paid_by':
            anomalies.append({
                'row_number': row_number,
                'field': field,
                'anomaly_type': 'missing_payer',
                'original_value': '',
                'corrected_value': '',
                'severity': 'critical',
                'auto_resolved': False,
                'description': f'Row {row_number}: Missing payer. Cannot determine who paid for this expense.',
            })
        return '', anomalies

    stripped = raw_name.strip()
    lookup = stripped.lower()

    # Check known names
    if lookup in KNOWN_NAMES:
        canonical = KNOWN_NAMES[lookup]
        if stripped != canonical:
            # Determine type of fix
            if lookup == stripped.lower() and stripped != canonical and lookup in ['aisha', 'rohan', 'priya', 'meera', 'dev', 'sam']:
                anomaly_type = 'name_case'
                desc = f'Row {row_number}: Name casing "{stripped}" normalized to "{canonical}".'
                severity = 'info'
            else:
                anomaly_type = 'name_variant'
                desc = f'Row {row_number}: Name variant "{stripped}" mapped to "{canonical}".'
                severity = 'warning'

            anomalies.append({
                'row_number': row_number,
                'field': field,
                'anomaly_type': anomaly_type,
                'original_value': stripped,
                'corrected_value': canonical,
                'severity': severity,
                'auto_resolved': True,
                'description': desc,
            })
        return canonical, anomalies

    # Check if it contains a known name (e.g., "Dev's friend Kabir")
    for known_lower, canonical in KNOWN_NAMES.items():
        if known_lower in lookup and lookup != known_lower:
            # This is a non-member participant
            anomalies.append({
                'row_number': row_number,
                'field': field,
                'anomaly_type': 'non_member',
                'original_value': stripped,
                'corrected_value': stripped,
                'severity': 'warning',
                'auto_resolved': False,
                'description': f'Row {row_number}: "{stripped}" is not a recognized group member. They will be added as a guest participant.',
            })
            return stripped, anomalies

    # Unknown name — flag as non-member
    title_cased = stripped.title()
    if title_cased != stripped:
        anomalies.append({
            'row_number': row_number,
            'field': field,
            'anomaly_type': 'name_case',
            'original_value': stripped,
            'corrected_value': title_cased,
            'severity': 'info',
            'auto_resolved': True,
            'description': f'Row {row_number}: Name "{stripped}" normalized to "{title_cased}".',
        })

    # Check if genuinely unknown
    if lookup not in KNOWN_NAMES:
        # Could be a guest like "Kabir" or unknown
        is_known_variant = False
        for known in KNOWN_NAMES.values():
            if known.lower() == lookup:
                is_known_variant = True
                break
        if not is_known_variant and lookup not in ['kabir']:
            anomalies.append({
                'row_number': row_number,
                'field': field,
                'anomaly_type': 'non_member',
                'original_value': stripped,
                'corrected_value': title_cased,
                'severity': 'warning',
                'auto_resolved': False,
                'description': f'Row {row_number}: "{stripped}" is not a recognized group member.',
            })

    return title_cased, anomalies
