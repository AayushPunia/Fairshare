"""
Seed script — pre-populate the database with the 6 flatmates.

Usage:
    python manage.py shell < seed.py

Creates users with password = lowercase username for easy demo login.
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User
from rest_framework.authtoken.models import Token

USERS = [
    {'username': 'aisha', 'display_name': 'Aisha', 'email': 'aisha@fairshare.app'},
    {'username': 'rohan', 'display_name': 'Rohan', 'email': 'rohan@fairshare.app'},
    {'username': 'priya', 'display_name': 'Priya', 'email': 'priya@fairshare.app'},
    {'username': 'meera', 'display_name': 'Meera', 'email': 'meera@fairshare.app'},
    {'username': 'dev',   'display_name': 'Dev',   'email': 'dev@fairshare.app'},
    {'username': 'sam',   'display_name': 'Sam',   'email': 'sam@fairshare.app'},
]


def seed():
    print('Seeding users...')
    for user_data in USERS:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'display_name': user_data['display_name'],
                'email': user_data['email'],
                'first_name': user_data['display_name'],
            }
        )
        if created:
            user.set_password(user_data['username'])  # password = username
            user.save()
            Token.objects.get_or_create(user=user)
            print(f'  Created: {user.display_name} (password: {user.username})')
        else:
            print(f'  Exists:  {user.display_name}')

    print(f'\nDone! {User.objects.count()} users in database.')
    print('Login credentials: username = password (e.g., aisha/aisha)')


if __name__ == '__main__':
    seed()
else:
    seed()
