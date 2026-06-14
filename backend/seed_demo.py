"""
Demo seed script — creates users + demo group with correct membership timeline.

Usage:
    python seed_demo.py

Creates:
- 6 flatmates with password = lowercase username
- "Flat 42" group with correct membership dates
- Meera leaves end of March, Sam joins April 8
"""

import os
import sys
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import User
from groups.models import Group, GroupMember
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
    print('=' * 50)
    print('FairShare Demo Seed')
    print('=' * 50)

    # 1. Create users
    print('\n1. Seeding users...')
    users = {}
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
            user.set_password(user_data['username'])
            user.save()
            Token.objects.get_or_create(user=user)
            print(f'  ✓ Created: {user.display_name} (password: {user.username})')
        else:
            print(f'  · Exists:  {user.display_name}')
        users[user_data['username']] = user

    # 2. Create demo group
    print('\n2. Creating demo group...')
    group, created = Group.objects.get_or_create(
        name='Flat 42',
        defaults={
            'description': 'Shared flat expenses for 2026',
            'default_currency': 'INR',
            'created_by': users['aisha'],
        }
    )
    if created:
        print(f'  ✓ Created group: {group.name}')
    else:
        print(f'  · Group already exists: {group.name}')
        return

    # 3. Add members with correct timeline
    print('\n3. Adding members with timeline...')
    members = [
        # Original members from Feb 1
        {'user': 'aisha', 'joined': date(2026, 2, 1), 'left': None},
        {'user': 'rohan', 'joined': date(2026, 2, 1), 'left': None},
        {'user': 'priya', 'joined': date(2026, 2, 1), 'left': None},
        # Meera leaves end of March
        {'user': 'meera', 'joined': date(2026, 2, 1), 'left': date(2026, 3, 31)},
        # Sam joins April 8
        {'user': 'sam',   'joined': date(2026, 4, 8), 'left': None},
    ]

    for m in members:
        user = users[m['user']]
        is_active = m['left'] is None
        member, created = GroupMember.objects.get_or_create(
            group=group,
            user=user,
            defaults={
                'joined_at': m['joined'],
                'left_at': m['left'],
                'is_active': is_active,
            }
        )
        status = 'active' if is_active else f'left {m["left"]}'
        print(f'  {"✓" if created else "·"} {user.display_name}: joined {m["joined"]}, {status}')

    # Note: Dev is NOT added as a permanent member — he's a guest
    print(f'\n  Note: Dev is a guest (not a permanent group member).')
    print(f'  He appears in expenses when visiting.')

    print(f'\n{"=" * 50}')
    print(f'Done! {User.objects.count()} users, {Group.objects.count()} group(s)')
    print(f'Login: username = password (e.g., aisha/aisha)')
    print(f'{"=" * 50}')


if __name__ == '__main__':
    seed()
else:
    seed()
