from django.core.management.base import BaseCommand, CommandError
from telegram.ext import Updater
import logging
from telegram.ext import MessageHandler, Filters, CommandHandler
import os
from hello.models import Chats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

WELCOME_MESSAGE = os.environ.get('MESSAGE_WELCOME')


def start(update, context):
    chat_id = update.effective_chat.id
    Chats.objects.update_or_create(chat_id=chat_id, user_requested_stop=False)
    context.bot.send_message(chat_id=chat_id,
                             text=WELCOME_MESSAGE)


def stop(update, context):
    chat_id = update.effective_chat.id

    Chats.objects.update_or_create(chat_id=chat_id, user_requested_stop=True)

    context.bot.send_message(chat_id=chat_id,
                             text="Stopping the spam. To keep going, send /start")


def help_command(update, context):
    logging.info("got help")
    context.bot.send_message(chat_id=update.effective_chat.id, text="I don't know that command. Try /start or /stop")


def error_handler(update, error_msg):
    logging.warning('Update "%s" caused error "%s"', update, error_msg)


class Command(BaseCommand):
    help = 'Runs the telegram bot'

    def add_arguments(self, parser):
        parser.add_argument("--first-run", action="store_true", help="Initialise files for first run")
        parser.add_argument("--purge-data", action="store_true", help="Deletes any data files during initialisation")
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
        dp.add_handler(CommandHandler('start', start))
        dp.add_handler(CommandHandler('stop', stop))
        dp.add_handler(MessageHandler(Filters.text, help_command))
        dp.add_error_handler(error_handler)

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
