from app.settings import ALLOWED_HOSTS

from django.core.signing import Signer
from django.template.loader import render_to_string

signer = Signer()


def send_activation_notification(user):
    if ALLOWED_HOSTS:
        host = f'http://{ALLOWED_HOSTS[0]}'
    else:
        host = 'http://localhost:8000'

    context = {'user': user, 'host': host, 'sign': signer.sign(user.username)}

    subject = render_to_string('email/activation_letter_subject', context)
    body = render_to_string('email/activation_letter_body', context)

    user.email_user(subject, body)
