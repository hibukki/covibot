import datetime

from django.core.management.base import BaseCommand, CommandError
from telegram import ReplyKeyboardMarkup, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, ConversationHandler, CallbackQueryHandler
import logging
from telegram.ext import MessageHandler, Filters, CommandHandler
import os

from hello.common import get_env_message
from hello.models import Chats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


HOUR = range(1)

hours = [str(x) + ":00" for x in list(range(0, 24))]
hours = hours[8:] + hours[:8]
reply_keyboard = [hours[x:x+4] for x in range(0, 24, 4)]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

inline_menu = InlineKeyboardMarkup([
    [InlineKeyboardButton("שנה שעה", callback_data='hour')],
    [InlineKeyboardButton("בטל תזכורת", callback_data='cancel')]
])

inline_hours = [InlineKeyboardButton(str(x) + ":00", callback_data=x) for x in list(range(0, 24))]
inline_hours = inline_hours[8:] + inline_hours[:8]
inline_keyboard = [inline_hours[x:x+4] for x in range(0, 24, 4)]
inline_markup = InlineKeyboardMarkup(inline_keyboard)


def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, [header_buttons])
    if footer_buttons:
        menu.append([footer_buttons])
    return menu


button_list = [
    InlineKeyboardButton("col1", callback_data="callback data col1"),
    InlineKeyboardButton("col2", callback_data="callback data col2"),
    InlineKeyboardButton("row 2", callback_data="callback data row2")
]

reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))


def start_message_handler(update, context):
    chat_id = update.effective_chat.id
    Chats.objects.update_or_create(chat_id=chat_id, defaults={'user_requested_stop': False})

    context.bot.send_message(chat_id=chat_id,
                             text=get_env_message('MESSAGE_WELCOME'))
    logging.info(f"Start reply: {HOUR}")

    return ask_for_hour(update, context)


def ask_for_hour(update, context):
    update.message.reply_text("מתי תרצה לקבל את ההתראה היומית שלך?", reply_markup=inline_markup)


def get_message_thank_you_for_picking_hour(chosen_hour):
    return "מעולה!\n"\
           "נשלח לך לכאן כל יום בשעה *{}* התראה על מנת למלא את הטופס!\n\nכדי להתחיל מחדש, שלחו /start"\
        .format(chosen_hour)


def hour(update, context):
    hour = update.message.text
    # user = update.message.from_user
    # chat_id = update.message.chat_id
    # set_user_updates(user, chat_id, hour)
    update.message.reply_text(
        get_message_thank_you_for_picking_hour(hour),
        parse_mode=ParseMode.MARKDOWN)

    return ConversationHandler.END


def stop_message_handler(update, context):
    chat_id = update.effective_chat.id

    Chats.objects.update_or_create(chat_id=chat_id, defaults={"user_requested_stop": True})

    context.bot.send_message(chat_id=chat_id,
                             text=get_env_message('MESSAGE_STOPPED'))


def unknown_command_handler(update, context):
    logging.info("got help")
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=get_env_message('MESSAGE_UNKNOWN_COMMAND'))


def bot_error_handler(update, context):
    logging.warning('Update "%s" caused error "%s"', update, context.error)


def cancel(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(text="התזכורת היומית בוטלה! לחץ /start על מנת להירשם מחדש.")

    # TODO - Delete from database


def change_hour(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text("מתי תרצה לקבל את ההתראה היומית שלך?", reply_markup=inline_markup)


def menu_choice(update, context):
    logging.info(f"menu_choice called")
    query = update.callback_query
    command = query.data
    if command == 'cancel':
        return cancel(update, context)
    elif command == 'hour':
        return change_hour(update, context)
    elif command == 'clicked':
        # TODO - Updated clicks/last clicked
        query.answer()
        return
    return choose_hour(update, context)


def set_user_updates(user, chat_id, hour):
    user_name = user.username
    # TODO - save to database

    return


def choose_hour(update, context):
    query = update.callback_query
    selected_hour = int(query.data)
    user = query.message.from_user
    chat_id = query.message.chat_id
    set_user_updates(user, chat_id, hour)
    query.answer()

    query.edit_message_text(text=get_message_thank_you_for_picking_hour(selected_hour),
                            parse_mode=ParseMode.MARKDOWN,
                            # reply_markup=inline_menu
                            )

    chat_id = update.effective_chat.id

    requested_reminder_time = datetime.time(selected_hour, 0, 0)
    logging.info(f"Setting time to {requested_reminder_time}")

    Chats.objects.filter(chat_id=chat_id).update(requested_reminder_time=requested_reminder_time)


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
        dp.add_handler(CallbackQueryHandler(menu_choice))
        dp.add_handler(CommandHandler('stop', stop_message_handler))
        # dp.add_handler(MessageHandler(Filters.text, unknown_command_handler))
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
