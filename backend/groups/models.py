from django.db import models
from django.conf import settings


class Group(models.Model):
    """
    A group of flatmates who share expenses.
    Each group has its own set of expenses, members, and settlements.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    default_currency = models.CharField(max_length=3, default='INR')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_groups'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def active_members(self, as_of_date=None):
        """Return members active on a given date (or currently active)."""
        qs = self.memberships.all()
        if as_of_date:
            qs = qs.filter(joined_at__lte=as_of_date)
            qs = qs.filter(
                models.Q(left_at__isnull=True) | models.Q(left_at__gte=as_of_date)
            )
        else:
            qs = qs.filter(is_active=True)
        return qs


class GroupMember(models.Model):
    """
    Tracks membership in a group, including join and leave dates.
    This is critical for:
    - Sam: joined mid-April, shouldn't owe for March expenses
    - Meera: left end of March, shouldn't owe for April expenses
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships'
    )
    joined_at = models.DateField()
    left_at = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['group', 'user', 'joined_at']
        ordering = ['joined_at']

    def __str__(self):
        status = 'active' if self.is_active else f'left {self.left_at}'
        return f'{self.user.display_name} in {self.group.name} ({status})'

    def was_active_on(self, date):
        """Check if this member was active on a specific date."""
        if date < self.joined_at:
            return False
        if self.left_at and date > self.left_at:
            return False
        return True
