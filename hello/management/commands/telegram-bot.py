import datetime
import logging
import os
from django.core.management.base import BaseCommand
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler

from hello.common import get_env_message
from hello.models import Chats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


def get_hour_selection_keyboard():
    inline_hours = [InlineKeyboardButton(str(x) + ":00", callback_data=x) for x in list(range(0, 24))]
    inline_hours = inline_hours[8:] + inline_hours[:8]
    hour_selection_keyboard = [inline_hours[x:x + 4] for x in range(0, 24, 4)]
    return InlineKeyboardMarkup(hour_selection_keyboard)


def start_message_handler(update, context):
    chat_id = update.effective_chat.id

    # Save user to DB
    Chats.objects.update_or_create(chat_id=chat_id, defaults={'user_requested_stop': False})

    # Send Welcome
    context.bot.send_message(chat_id=chat_id, text=get_env_message('MESSAGE_WELCOME'))

    # Ask for hour selection
    update.message.reply_text("מתי תרצה לקבל את ההתראה היומית שלך?", reply_markup=get_hour_selection_keyboard())


def stop_message_handler(update, context):
    chat_id = update.effective_chat.id

    Chats.objects.update_or_create(chat_id=chat_id, defaults={"user_requested_stop": True})

    context.bot.send_message(chat_id=chat_id,
                             text=get_env_message('MESSAGE_STOPPED'))


def unknown_command_handler(update, context):
    logging.info("got unknown command")
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=get_env_message('MESSAGE_UNKNOWN_COMMAND'))


def bot_error_handler(update, context):
    logging.warning('Update "%s" caused error "%s"', update, context.error)


def cancel(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="התזכורת היומית בוטלה! לחץ /start על מנת להירשם מחדש.")

    # TODO - Delete from database. Maybe call stop_message_handler() ?


def change_hour(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text("מתי תרצה לקבל את ההתראה היומית שלך?", reply_markup=get_hour_selection_keyboard())


def menu_item_selected_handler(update, context):
    logging.info(f"menu_choice called")
    # query = update.callback_query
    # command = query.data
    # if command == 'cancel':
    #     return cancel(update, context)

    # The only menu item supported is selecting an hour
    return user_selected_hour(update, context)


def user_selected_hour(update, context):
    query = update.callback_query
    selected_hour = int(query.data)
    query.answer()

    # Send: Time selected
    query.edit_message_text(text="מעולה!\n"
                                 "נשלח לך לכאן כל יום בשעה *{}* התראה על מנת למלא את הטופס!"
                                 "\n\nכדי להתחיל מחדש, שלחו /start".format(selected_hour),
                            parse_mode=ParseMode.MARKDOWN)

    # Save time selection to DB
    chat_id = update.effective_chat.id
    requested_reminder_time = datetime.time(selected_hour, 0, 0)
    logging.info(f"Setting time to {requested_reminder_time}")
    Chats.objects.filter(chat_id=chat_id).update(requested_reminder_time=requested_reminder_time)


class Command(BaseCommand):
    help = 'Runs the telegram bot, listens for new messages'

    def add_arguments(self, parser):
        parser.add_argument("--local", action="store_true", help="For running locally, not deployed to Heroku")

    def handle(self, *args, **options):
        logging.info("Running telegram-bot")
        TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_TOKEN')

        # Set up the Updater
        updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
        dp = updater.dispatcher

        # How to handle each message
        dp.add_handler(CommandHandler('start', start_message_handler))
        dp.add_handler(CallbackQueryHandler(menu_item_selected_handler))
        dp.add_handler(CommandHandler('stop', stop_message_handler))
        dp.add_error_handler(bot_error_handler)

        # Running on Heroku?
        if not options['local']:
            HEROKU_PORT = os.environ.get('PORT')
            HEROKU_APP_NAME = "covibot"  # App name on Heroku

            # Start the webhook
            updater.start_webhook(listen="0.0.0.0",
                                  port=int(HEROKU_PORT),
                                  url_path=TELEGRAM_BOT_TOKEN)
            updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(HEROKU_APP_NAME, TELEGRAM_BOT_TOKEN))
        else:
            # Running locally
            updater.start_polling()

        logging.info(f"Running until interrupt...")
        updater.idle()
