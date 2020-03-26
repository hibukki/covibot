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

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')

updater = Updater(token=os.environ.get('TELEGRAM_TOKEN'), use_context=True)

dispatcher = updater.dispatcher


def start_how_are_you(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"{QUESTION}\n{SURVEY_URL}")
    logging.info("start_how_are_you")
    threading.Timer(10, start_how_are_you, [update, context]).start()


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

    start_how_are_you(update, context)


def echo(update, context):
    logging.info("got echo")
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def caps(update, context):
    logging.info("got caps")
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

caps_handler = CommandHandler('caps', caps)
dispatcher.add_handler(caps_handler)

echo_handler = MessageHandler(Filters.text, echo)
dispatcher.add_handler(echo_handler)

updater.start_polling()
