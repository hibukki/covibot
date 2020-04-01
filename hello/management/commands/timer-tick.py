import datetime

import pytz
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
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
        TOKEN = os.environ.get('TELEGRAM_TOKEN')

        tz = pytz.timezone('Israel')
        # now = timezone.make_aware(datetime.datetime.now(), tz).astimezone(timezone.utc)
        now = datetime.datetime.now().astimezone(tz)
        current_hour = now.hour
        self.stdout.write(f"Timer tick {now} ({current_hour})")

        # Set up the Updater
        updater = Updater(TOKEN, use_context=True)

        for chat in Chats.objects\
                .filter(Q(user_requested_stop=False) &
                        Q(requested_reminder_time__hour=current_hour))\
                .all():

            logging.info(f"Requested time for this chat: {chat.requested_reminder_time}")

            self.stdout.write(f"Sending to chat: {chat}")
            updater.bot.send_message(chat_id=chat.chat_id,
                                     text=get_env_message('MESSAGE_REMINDER'))

        self.stdout.write(f"Done. Skipped: {Chats.objects.filter(user_requested_stop=True).count()}")
