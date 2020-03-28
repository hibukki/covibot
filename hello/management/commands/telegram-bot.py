from django.core.management.base import BaseCommand, CommandError
from telegram.ext import Updater
import logging
from telegram.ext import MessageHandler, Filters, PicklePersistence, CommandHandler
import threading
import os
import boto3

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

SURVEY_URL = "https://coronaisrael.org/"
QUESTION = "הגיע הזמן למלא את הסקר שיעזור לנו לנצח את הקורונה:"
KEEP_GOING = "keep_going"

exiting = False


def start_how_are_you(update, context):
    try:
        should_keep_going = context.user_data[KEEP_GOING]
        if not should_keep_going:
            return
    except KeyError:
        logging.warning(f"user_data doesn't contain key {KEEP_GOING}")
        return

    if exiting:
        logging.info("Script is exiting, so aborting start_how_are_you")
        return

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"{QUESTION}\n{SURVEY_URL}.\nTo stop, send: /stop")
    logging.info("start_how_are_you")

    # TODO: Use a job instead:
    # https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/timerbot.py
    threading.Timer(10, start_how_are_you, [update, context]).start()


def start(update, context):
    context.user_data[KEEP_GOING] = True
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="This is a draft covid-19 questionnaire!")

    start_how_are_you(update, context)


def stop(update, context):
    context.user_data[KEEP_GOING] = False
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Stopping the spam. To keep going, send /start")

    start_how_are_you(update, context)


def help_command(update, context):
    logging.info("got help")
    context.bot.send_message(chat_id=update.effective_chat.id, text="I don't know that command. Try /start or /stop")
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def caps(update, context):
    logging.info("got caps")
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


def error(bot, update, error_msg):
    logging.warning('Update "%s" caused error "%s"', update, error_msg)


class Command(BaseCommand):
    help = 'Runs the telegram bot'

    def add_arguments(self, parser):
        parser.add_argument("--first-run", action="store_true", help="Initialise files for first run")
        parser.add_argument("--purge-data", action="store_true", help="Deletes any data files during initialisation")
        parser.add_argument("--local", action="store_true", help="For running locally, not deployed to Heroku")

    def handle(self, *args, **options):
        self.stdout.write("Running a management command, OMG!")
        # if __name__ == "__main__":
        TOKEN = os.environ.get('TELEGRAM_TOKEN')
        NAME = "covibot"  # App name on Heroku

        # Port is given by Heroku
        PORT = os.environ.get('PORT')

        INSTANCE_ID = os.environ["INSTANCE_ID"]

        # Set name of persistence data file
        persistence_file = "persistence.pickle"

        # Define parser
        # parser = argparse.ArgumentParser(description='JioBot Telegram Bot')

        # Add optional argument

        # Parse args
        # args = parser.parse_args()
        logging.info(f"Parsed arguments: {options}")

        # Create AWS S3 resource object
        s3 = boto3.resource('s3')

        # Removes local copy of persistence file if desired
        if options['purge_data']:
            logging.warning(
                f"Local persistence file will be deleted (if it even exists) since --purge-data={options['purge_data']}")

            # Remove file
            logging.info(f"Checking for existence of {persistence_file}")
            if os.path.isfile(persistence_file):
                logging.info(f"File {persistence_file} was found!")
                os.remove(persistence_file)
                logging.info(f"Deleted {persistence_file}")

        # Check if persistence file exists
        if True:  # not os.path.isfile(persistence_file):
            logging.error(f"(doing as if) File {persistence_file} was not found!")

            # Warn that new file will be created
            if options['first_run']:
                logging.warning(
                    f"File {persistence_file} will be newly created since --first-run={options['first_run']}")

            # Get file from AWS S3 if not first time
            else:
                s3.meta.client.download_file(INSTANCE_ID, persistence_file, persistence_file)
                logging.info(f"File {persistence_file} was successfully downloaded!")

        # Initialise persistence object
        pp = PicklePersistence(filename=persistence_file)

        # Set up the Updater
        updater = Updater(TOKEN, persistence=pp, use_context=True)
        dp = updater.dispatcher
        # Add handlers
        dp.add_handler(CommandHandler('start', start))
        dp.add_handler(CommandHandler('stop', stop))
        dp.add_handler(MessageHandler(Filters.text, help_command))
        dp.add_error_handler(error)

        logging.info(f"Listening for messages... Does persistence file exist? {os.path.isfile(persistence_file)}")

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
            exiting = True
            logging.info(f"Exiting...")

        if (os.path.isfile(persistence_file)):
            # Backup latest file to AWS
            logging.info(f"Uploading {persistence_file} to AWS S3.")
            s3.meta.client.upload_file(persistence_file, INSTANCE_ID, persistence_file)
            logging.info(f"File {persistence_file} was successfully uploaded!")
        else:
            logging.info(f"Didn't find pickle file {persistence_file} for uploading to AWS S3.")
