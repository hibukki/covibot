from django.core.management.base import BaseCommand, CommandError
from telegram.ext import Updater
import logging
import os
from hello.models import Chats


class Command(BaseCommand):
    help = 'Removes all chats from DB'

    def handle(self, *args, **options):
        Chats.objects.all().delete()
