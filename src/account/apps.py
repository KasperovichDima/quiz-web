from account.utils import send_activation_notification

from django.apps import AppConfig
from django.dispatch import Signal


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'


def user_registered_dispatcher(sender, **kwargs):
    send_activation_notification(kwargs['instance'])


user_registered = Signal()
user_registered.connect(user_registered_dispatcher)
