from django.core.management.base import BaseCommand, CommandError
from telegram.ext import Updater
import logging
import os
from hello.models import Chats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

SURVEY_URL = "https://coronaisrael.org/"
QUESTION = "הגיע הזמן למלא את הסקר שיעזור לנו לנצח את הקורונה:"


class Command(BaseCommand):
    help = 'Runs the telegram bot'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        self.stdout.write("Timer tick")
        # if __name__ == "__main__":
        TOKEN = os.environ.get('TELEGRAM_TOKEN')

        # Set up the Updater
        updater = Updater(TOKEN, use_context=True)

        for chat in Chats.objects.filter(user_requested_stop=False).all():
            updater.bot.send_message(chat_id=chat.chat_id,
                                     text=f"{QUESTION}\n{SURVEY_URL}.\n\nTo stop, send: /stop")
