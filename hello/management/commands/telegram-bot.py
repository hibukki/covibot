from django.core.management.base import BaseCommand, CommandError
from telegram.ext import Updater
import logging
from telegram.ext import MessageHandler, Filters, CommandHandler
import os

from hello.common import get_env_message
from hello.models import Chats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def start_message_handler(update, context):
    chat_id = update.effective_chat.id
    Chats.objects.update_or_create(chat_id=chat_id, defaults={"user_requested_stop": False})

    context.bot.send_message(chat_id=chat_id,
                             text=get_env_message('MESSAGE_WELCOME'))


def stop_message_handler(update, context):
    chat_id = update.effective_chat.id

    Chats.objects.update_or_create(chat_id=chat_id, user_requested_stop=True)

    context.bot.send_message(chat_id=chat_id,
                             text=get_env_message('MESSAGE_STOPPED'))


def unknown_command_handler(update, context):
    logging.info("got help")
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=get_env_message('MESSAGE_UNKNOWN_COMMAND'))


def bot_error_handler(update, context):
    logging.warning('Update "%s" caused error "%s"', update, context.error)


class Command(BaseCommand):
    help = 'Runs the telegram bot'

    def add_arguments(self, parser):
        parser.add_argument("--local", action="store_true", help="For running locally, not deployed to Heroku")

    def handle(self, *args, **options):
        self.stdout.write("Running a management command, OMG! 2")
        # if __name__ == "__main__":
        TOKEN = os.environ.get('TELEGRAM_TOKEN')
        NAME = "covibot"  # App name on Heroku

        # Port is given by Heroku
        PORT = os.environ.get('PORT')

        # Set up the Updater
        updater = Updater(TOKEN, use_context=True)
        dp = updater.dispatcher
        # Add handlers
        dp.add_handler(CommandHandler('start', start_message_handler))
        dp.add_handler(CommandHandler('stop', stop_message_handler))
        dp.add_handler(MessageHandler(Filters.text, unknown_command_handler))
        dp.add_error_handler(bot_error_handler)

        # Running on Heroku?
        if not options['local']:
            # Start the webhook
            updater.start_webhook(listen="0.0.0.0",
                                  port=int(PORT),
                                  url_path=TOKEN)
            updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))

            # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
            # SIGTERM or SIGABRT
            updater.idle()
        else:  # Running locally
            updater.start_polling()
            logging.info(f"Running until interrupt...")
            updater.idle()
            logging.info(f"Exiting...")
