from django.db import models
from django.conf import settings
from decimal import Decimal


class Expense(models.Model):
    """
    A shared expense within a group.

    Supports four split types as found in the CSV:
    - equal: amount / count(participants)
    - unequal: explicit amounts per participant
    - percentage: amount × (percentage / 100)
    - share: amount × (user_shares / total_shares)

    Currency handling:
    - amount: the original amount in the original currency
    - currency: 'INR' or 'USD'
    - amount_inr: converted amount in INR (for balance calculations)
    - exchange_rate: the rate used for conversion (1.0 for INR)

    is_settlement: True for rows that are payments between members,
    not real expenses (e.g., "Rohan paid Aisha back", "Sam deposit share")
    """

    SPLIT_TYPES = [
        ('equal', 'Equal'),
        ('unequal', 'Unequal'),
        ('percentage', 'Percentage'),
        ('share', 'Share'),
    ]

    group = models.ForeignKey(
        'groups.Group', on_delete=models.CASCADE, related_name='expenses'
    )
    description = models.CharField(max_length=500)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expenses_paid'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    amount_inr = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Amount in INR for balance calculations'
    )
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal('1.0'),
        help_text='Exchange rate to INR (1.0 for INR expenses)'
    )
    split_type = models.CharField(max_length=20, choices=SPLIT_TYPES, default='equal')
    date = models.DateField()
    notes = models.TextField(blank=True, default='')
    is_settlement = models.BooleanField(
        default=False,
        help_text='True if this is a payment/settlement, not a real expense'
    )
    import_session = models.ForeignKey(
        'importer.ImportSession',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='imported_expenses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.description} - {self.currency} {self.amount} ({self.date})'


class ExpenseSplit(models.Model):
    """
    How an expense is split among participants.
    Each row represents one participant's share of an expense.
    share_amount is always in INR for consistent balance calculations.
    """
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expense_splits'
    )
    share_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text='Amount this user owes in INR'
    )
    share_percentage = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Percentage share (for percentage splits)'
    )
    share_units = models.IntegerField(
        null=True, blank=True,
        help_text='Number of share units (for share-based splits)'
    )

    class Meta:
        unique_together = ['expense', 'user']

    def __str__(self):
        return f'{self.user.display_name}: ₹{self.share_amount} for {self.expense.description}'


class Settlement(models.Model):
    """
    A direct payment from one user to another to settle debts.
    Separate from Expense to keep the data model clean.
    """
    group = models.ForeignKey(
        'groups.Group', on_delete=models.CASCADE, related_name='settlements'
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settlements_paid'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settlements_received'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    date = models.DateField()
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.from_user.display_name} → {self.to_user.display_name}: ₹{self.amount}'
