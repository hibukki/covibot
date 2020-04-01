import datetime

from django.db import models


# Create your models here.
class Greeting(models.Model):
    when = models.DateTimeField("date created", auto_now_add=True)


class Chats(models.Model):
    # Docs: https://python-telegram-bot.readthedocs.io/en/stable/telegram.chat.html#telegram.Chat.id
    chat_id = models.IntegerField("python-telegram-bot chat id", primary_key=True)
    user_requested_stop = models.BooleanField("User asked to stop", default=False)
    requested_reminder_time = models.TimeField(blank=True, null=True)



