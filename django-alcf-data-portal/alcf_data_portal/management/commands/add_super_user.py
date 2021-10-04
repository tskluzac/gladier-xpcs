from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Make a user a super user'

    def add_arguments(self, parser):
        parser.add_argument('--users', nargs='+', required=False)

    def handle(self, *args, **options):
        users = options.get('users')
        if users:
            for user in users:
                u = User.objects.filter(username=user).first()
                if not u:
                    self.stderr.write(f'User {u.username} does not exist!')
                    continue
                if u.is_staff and u.is_superuser:
                    self.stderr.write(f'User {u.username} is already a '
                                      f'superuser!')
                    continue
                u.is_staff = True
                u.is_superuser = True
                u.save()
                self.stdout.write(f'{u.username} is now a superuser')

        else:
            existing = ', '.join([u.username for u in User.objects.all()])
            self.stderr.write(f'Users: {existing}')
