from django.core.management.base import BaseCommand, CommandError
from telegram.ext import Updater
import logging
import os
from hello.models import Chats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

REMINDER_MESSAGE = os.environ.get('MESSAGE_REMINDER')


class Command(BaseCommand):
    help = 'Runs every time the heroku-scheduler ticks'

    def handle(self, *args, **options):
        self.stdout.write("Timer tick")
        TOKEN = os.environ.get('TELEGRAM_TOKEN')

        # Set up the Updater
        updater = Updater(TOKEN, use_context=True)

        for chat in Chats.objects.filter(user_requested_stop=False).all():
            updater.bot.send_message(chat_id=chat.chat_id,
                                     text=REMINDER_MESSAGE)
