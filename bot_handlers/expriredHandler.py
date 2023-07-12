import datetime
import time

from aiogram import types

from config.botConfig import config, bot
from database.query import get_expired_users


async def scheduler_expired_notifier():
    while True:
        if datetime.datetime.now().hour == 20:
            users_expired = get_expired_users(config)
            for user in users_expired:
                await bot.send_message(user[0],
                                       "Your <b>Api key will be Expire after 1 day.</b> \nPlease, send to me New key. "
                                       "\nElse, bot won`t work",
                                       parse_mode=types.ParseMode.HTML
                                       )
            time.sleep(86400)
        else:
            time.sleep(3600)
