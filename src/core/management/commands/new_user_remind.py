from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Remind new user, if no activity"

    def handle(self, *args, **options):
        today = timezone.now()
        yesterday = today - timedelta(1)
        users = get_user_model().objects.filter(date_joined__range=[yesterday, today])
        subject = 'Quiz needs your activity!'

        for user in users:
            if not user.results.all():
                message = f'Dear {user.get_full_name()}! We want to remind you, ' \
                          f'that our supa-dupa-mega quiz site is waiting for you! ' \
                          f'We miss you so much((( ' \
                          f'PS: And your money...'
                user.email_user(subject, message, 'noreply@quiz.com')
                self.stdout.write(f"E-mail notification to {user.username} was sent.")

        self.stdout.write('Reminding complete!')