from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for flatmates.
    Extends Django's AbstractUser to add display_name for flexible name rendering.
    """
    display_name = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.first_name or self.username
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name or self.username
