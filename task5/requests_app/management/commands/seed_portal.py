from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from requests_app.models import UserSettings


class Command(BaseCommand):
    help = 'Создает демо-пользователей для портала заявок'

    def handle(self, *args, **options):
        users = [
            ('employee', 'user', 'employee@example.com'),
            ('moderator', 'moderator', 'moderator@example.com'),
            ('adminportal', 'admin', 'admin@example.com'),
        ]
        for username, role, email in users:
            user, created = User.objects.get_or_create(username=username, defaults={'email': email})
            if created:
                user.set_password('portal12345')
                user.save()
            user.profile.role = role
            user.profile.save()
            UserSettings.objects.get_or_create(user=user)
        admin_user = User.objects.get(username='adminportal')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save(update_fields=['is_staff', 'is_superuser'])
        self.stdout.write(self.style.SUCCESS('Демо-пользователи созданы: employee, moderator, adminportal'))
