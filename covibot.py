from telegram.ext import Updater
import logger
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import threading
import os

logger.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   level=logger.INFO)

SURVEY_URL = "https://coronaisrael.org/"
QUESTION = "הגיע הזמן למלא את הסקר שיעזור לנו לנצח את הקורונה:"


def start_how_are_you(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"{QUESTION}\n{SURVEY_URL}")
    logger.info("start_how_are_you")
    threading.Timer(10, start_how_are_you, [update, context]).start()


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

    start_how_are_you(update, context)


def echo(update, context):
    logger.info("got echo")
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def caps(update, context):
    logger.info("got caps")
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


if __name__ == "__main__":
    TOKEN = os.environ.get('TELEGRAM_TOKEN')
    NAME = "covibot"  # App name on Heroku

    # Port is given by Heroku
    PORT = os.environ.get('PORT')

    # Set up the Updater
    updater = Updater(TOKEN)
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
