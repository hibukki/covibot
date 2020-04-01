
from django.core.management.base import BaseCommand
import logging

from hello.models import Chats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.info(f"Starting. Stop=true in: {Chats.objects.filter(user_requested_stop=True).count()}")
        Chats.objects.filter(user_requested_stop=True).update(user_requested_stop=False)

        logging.info(f"Done. Stop=true in: {Chats.objects.filter(user_requested_stop=True).count()}")
