from celery import shared_task
from celery.utils.log import get_task_logger

from django.core.management import call_command

logger = get_task_logger(__name__)


@shared_task
def simple_task():
    logger.info(">>>>> THE SAMPLE TASK JUST RUN <<<<<")


@shared_task
def send_email_report():
    call_command('email_report')

@shared_task
def new_user_remind():
    call_command('new_user_remind')
