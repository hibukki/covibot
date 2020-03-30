from django.core.management.base import BaseCommand, CommandError
from telegram.ext import Updater
import logging
import os

from hello.common import get_env_message
from hello.models import Chats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


class Command(BaseCommand):
    help = 'Runs every time the heroku-scheduler ticks'

    def handle(self, *args, **options):
        self.stdout.write("Timer tick")
        TOKEN = os.environ.get('TELEGRAM_TOKEN')

        # Set up the Updater
        updater = Updater(TOKEN, use_context=True)

        for chat in Chats.objects.filter(user_requested_stop=False).all():
            self.stdout.write(f"Sending to chat: {chat}")
            updater.bot.send_message(chat_id=chat.chat_id,
                                     text=get_env_message('MESSAGE_REMINDER'))

        self.stdout.write(f"Done. Skipped: {Chats.objects.filter(user_requested_stop=True).count()}")
