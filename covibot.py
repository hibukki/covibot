from telegram.ext import Updater
import logging
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import threading
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   level=logging.INFO)

SURVEY_URL = "https://coronaisrael.org/"
QUESTION = "הגיע הזמן למלא את הסקר שיעזור לנו לנצח את הקורונה:"

# A way to stop the bot from spamming. TODO: Stop it per-user. Also, make the periodic mechanism better
keep_going = False


def start_how_are_you(update, context):
    if not keep_going:
        return

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"{QUESTION}\n{SURVEY_URL}. To stop, send: /stop")
    logging.info("start_how_are_you")
    threading.Timer(10, start_how_are_you, [update, context]).start()


def start(update, context):
    keep_going = True
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="This is a draft covid-19 questionair!")

    start_how_are_you(update, context)

def stop(update, context):
    keep_going = False
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Stopping the spam. To keep going, send /start")

    start_how_are_you(update, context)

def echo(update, context):
    logging.info("got echo")
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def caps(update, context):
    logging.info("got caps")
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"', update, error)


if __name__ == "__main__":
    TOKEN = os.environ.get('TELEGRAM_TOKEN')
    NAME = "covibot"  # App name on Heroku

    # Port is given by Heroku
    PORT = os.environ.get('PORT')

    # Set up the Updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    # Add handlers
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text, echo))
    dp.add_error_handler(error)

    # Start the webhook
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
    updater.idle()

# start_handler = CommandHandler('start', start)
# dispatcher.add_handler(start_handler)
#
# caps_handler = CommandHandler('caps', caps)
# dispatcher.add_handler(caps_handler)
#
# echo_handler = MessageHandler(Filters.text, echo)
# dispatcher.add_handler(echo_handler)
#
# updater.start_polling()
