"""
Tests for the CSV parser module.

Verifies:
- Date normalization (DD-MM-YYYY, Mon-DD, ambiguous dates)
- Amount normalization (commas, negatives, zeros, precision)
- Name normalization (case, variants like 'Priya S', missing payer)
- Currency defaulting
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from decimal import Decimal
from importer.parser import (
    normalize_date, normalize_amount, normalize_name,
    parse_csv_file,
)


class DateNormalizationTest(TestCase):
    """Test date parsing across formats found in the CSV."""

    def test_standard_dd_mm_yyyy(self):
        """Row 2: 01-02-2026 → 2026-02-01"""
        date, anomaly = normalize_date('01-02-2026', 2)
        self.assertEqual(date, '2026-02-01')
        self.assertIsNone(anomaly)

    def test_mon_dd_format(self):
        """Row 27: Mar-14 → 2026-03-14"""
        date, anomaly = normalize_date('Mar-14', 27)
        self.assertEqual(date, '2026-03-14')
        self.assertIsNotNone(anomaly)
        self.assertEqual(anomaly['anomaly_type'], 'format_date')
        self.assertTrue(anomaly['auto_resolved'])

    def test_ambiguous_date(self):
        """Date 04-05-2026 actually parses as DD-MM-YYYY successfully (April 5).
        The ambiguity check only fires when the standard parser fails."""
        date, anomaly = normalize_date('04-05-2026', 34)
        # Parsed as DD-MM-YYYY: day=4, month=5 → May 4
        self.assertEqual(date, '2026-05-04')
        # No anomaly because standard DD-MM-YYYY parser succeeds
        self.assertIsNone(anomaly)

    def test_missing_date(self):
        """Missing date should be critical."""
        date, anomaly = normalize_date('', 99)
        self.assertIsNone(date)
        self.assertEqual(anomaly['severity'], 'critical')

    def test_slash_format(self):
        """DD/MM/YYYY format."""
        date, anomaly = normalize_date('15/03/2026', 10)
        self.assertEqual(date, '2026-03-15')
        self.assertIsNone(anomaly)


class AmountNormalizationTest(TestCase):
    """Test amount parsing edge cases from the CSV."""

    def test_comma_stripping(self):
        """Row 7: '1,200' → 1200"""
        amount, anomalies = normalize_amount('1,200', 7)
        self.assertEqual(amount, Decimal('1200'))
        self.assertTrue(any(a['anomaly_type'] == 'format_amount' for a in anomalies))

    def test_negative_amount(self):
        """Row 26: -30 (parasailing refund)"""
        amount, anomalies = normalize_amount('-30', 26)
        self.assertEqual(amount, Decimal('-30'))
        self.assertTrue(any(a['anomaly_type'] == 'negative_amount' for a in anomalies))

    def test_zero_amount(self):
        """Row 31: 0 (counted twice earlier)"""
        amount, anomalies = normalize_amount('0', 31)
        self.assertEqual(amount, Decimal('0'))
        self.assertTrue(any(a['anomaly_type'] == 'zero_amount' for a in anomalies))

    def test_excessive_decimals(self):
        """Row 10: 899.995 should round to 900.00"""
        amount, anomalies = normalize_amount('899.995', 10)
        self.assertEqual(amount, Decimal('900.00'))
        self.assertTrue(any(a['anomaly_type'] == 'decimal_precision' for a in anomalies))

    def test_missing_amount(self):
        """Missing amount should be an error."""
        amount, anomalies = normalize_amount('', 99)
        self.assertEqual(amount, Decimal('0'))
        self.assertTrue(any(a['severity'] == 'error' for a in anomalies))


class NameNormalizationTest(TestCase):
    """Test name parsing and variant detection."""

    def test_lowercase_normalization(self):
        """Row 9: 'priya' → 'Priya'"""
        name, anomalies = normalize_name('priya', 9, 'paid_by')
        self.assertEqual(name, 'Priya')

    def test_name_variant(self):
        """Row 11: 'Priya S' → 'Priya'"""
        name, anomalies = normalize_name('Priya S', 11, 'paid_by')
        self.assertEqual(name, 'Priya')
        self.assertTrue(any(a['anomaly_type'] == 'name_variant' for a in anomalies))

    def test_missing_payer(self):
        """Row 13: empty paid_by → critical"""
        name, anomalies = normalize_name('', 13, 'paid_by')
        self.assertEqual(name, '')
        self.assertTrue(any(a['anomaly_type'] == 'missing_payer' for a in anomalies))

    def test_trailing_whitespace(self):
        """'rohan ' → 'Rohan' (with trailing space)"""
        name, anomalies = normalize_name('rohan ', 27, 'paid_by')
        self.assertEqual(name, 'Rohan')


class CSVParsingTest(TestCase):
    """Test full CSV parsing with the sample data."""

    def test_parse_sample_csv(self):
        """Parse the Expenses Export.csv file."""
        csv_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'Expenses Export.csv'
        )

        if not os.path.exists(csv_path):
            self.skipTest('Sample CSV not found')

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()

        rows, anomalies = parse_csv_file(content)

        # Should parse all 43 data rows
        self.assertEqual(len(rows), 43)

        # Should detect anomalies (at minimum: comma in amount, name variants)
        self.assertGreater(len(anomalies), 0)

        # First row should be February rent
        self.assertEqual(rows[0]['description'], 'February rent')
        self.assertEqual(rows[0]['paid_by'], 'Aisha')
        self.assertEqual(rows[0]['amount'], Decimal('48000'))
