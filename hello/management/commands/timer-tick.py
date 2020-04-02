import datetime
import logging
import os
import pytz
from django.core.management.base import BaseCommand
from django.db.models import Q
from telegram.ext import Updater

from hello.common import get_env_message
from hello.models import Chats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


class Command(BaseCommand):
    help = 'Run this every time the heroku-scheduler ticks'

    def handle(self, *args, **options):
        TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')

        # Get the time, now, in Israel
        tz = pytz.timezone('Israel')
        now = datetime.datetime.now().astimezone(tz)
        current_hour = now.hour
        logging.info(f"Timer tick {now} (hour: {current_hour})")

        updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

        # For each chat
        for chat in Chats.objects\
                .filter(Q(user_requested_stop=False) &
                        Q(requested_reminder_time__hour=current_hour))\
                .all():

            logging.debug(f"Sending to chat: {chat}")
            updater.bot.send_message(chat_id=chat.chat_id,
                                     text=get_env_message('MESSAGE_REMINDER'))

        logging.debug(f"Done. Users that asked to stop: {Chats.objects.filter(user_requested_stop=True).count()}")
