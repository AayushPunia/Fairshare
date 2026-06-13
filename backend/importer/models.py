from django.db import models
from django.conf import settings


class ImportSession(models.Model):
    """
    Tracks a CSV import session.
    Each upload creates one session that goes through: pending → reviewing → completed/failed.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    group = models.ForeignKey(
        'groups.Group', on_delete=models.CASCADE, related_name='import_sessions'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='import_sessions'
    )
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    raw_data = models.JSONField(
        default=list,
        help_text='Parsed CSV rows stored as JSON for review before commit'
    )
    total_rows = models.IntegerField(default=0)
    imported_rows = models.IntegerField(default=0)
    skipped_rows = models.IntegerField(default=0)
    anomalies_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Import {self.filename} ({self.status})'


class ImportAnomaly(models.Model):
    """
    Records every data problem detected during CSV import.
    This is the core of the import report — each anomaly has:
    - What was wrong (anomaly_type, original_value)
    - What we did about it (corrected_value, auto_resolved)
    - What the user decided (user_action)

    Severity levels:
    - info: Auto-fixed, FYI (e.g., stripped comma from amount)
    - warning: Needs review but has a suggested fix
    - error: Blocks this row from importing
    - critical: Blocks entire import until resolved
    """
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    ACTION_CHOICES = [
        ('pending', 'Pending'),
        ('auto_fixed', 'Auto Fixed'),
        ('user_approved', 'User Approved'),
        ('user_modified', 'User Modified'),
        ('skipped', 'Skipped'),
    ]
    ANOMALY_TYPES = [
        ('duplicate', 'Duplicate Entry'),
        ('format_amount', 'Amount Format Error'),
        ('format_date', 'Date Format Error'),
        ('name_case', 'Name Casing Issue'),
        ('name_variant', 'Name Variant'),
        ('missing_payer', 'Missing Payer'),
        ('missing_currency', 'Missing Currency'),
        ('settlement_as_expense', 'Settlement Logged as Expense'),
        ('percentage_sum', 'Percentage Sum Error'),
        ('negative_amount', 'Negative Amount (Refund)'),
        ('zero_amount', 'Zero Amount'),
        ('non_member', 'Non-Member Participant'),
        ('departed_member', 'Departed Member Included'),
        ('date_ambiguous', 'Ambiguous Date'),
        ('conflicting_split', 'Conflicting Split Info'),
        ('duplicate_conflict', 'Duplicate with Different Values'),
        ('decimal_precision', 'Excessive Decimal Precision'),
    ]

    import_session = models.ForeignKey(
        ImportSession, on_delete=models.CASCADE, related_name='anomalies'
    )
    row_number = models.IntegerField(help_text='1-indexed row number from CSV')
    field = models.CharField(max_length=50, help_text='Which CSV field has the issue')
    anomaly_type = models.CharField(max_length=30, choices=ANOMALY_TYPES)
    original_value = models.TextField(help_text='The original value from CSV')
    corrected_value = models.TextField(
        blank=True, default='',
        help_text='Suggested or auto-applied correction'
    )
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    auto_resolved = models.BooleanField(
        default=False,
        help_text='True if the system auto-fixed this (e.g., comma removal)'
    )
    user_action = models.CharField(
        max_length=20, choices=ACTION_CHOICES, default='pending'
    )
    description = models.TextField(
        help_text='Human-readable description of the anomaly'
    )
    ai_description = models.TextField(
        blank=True, default='',
        help_text='AI-generated enhanced description (Gemini)'
    )
    related_row = models.IntegerField(
        null=True, blank=True,
        help_text='Related row number for duplicates/conflicts'
    )

    class Meta:
        ordering = ['row_number', 'severity']

    def __str__(self):
        return f'Row {self.row_number}: {self.get_anomaly_type_display()} ({self.severity})'
