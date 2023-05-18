#!venv/bin/python
import asyncio

from aiogram import Dispatcher
from aiogram.dispatcher.filters import Text

from commands import Commands
from config.botConfig import dp
from bot_handlers.botHandler import cmd_start, cmd_pause_bot, cmd_edit_settings
from bot_handlers.mainHandler import cmd_start


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=Commands.START, state="*")


def register_handlers_main(dp: Dispatcher):
    dp.register_message_handler(cmd_start, Text(startswith=Commands.START_BOT), state="*")
    dp.register_message_handler(cmd_pause_bot, Text(startswith=Commands.PAUSE_BOT), state="*")
    dp.register_message_handler(cmd_edit_settings, Text(startswith=Commands.START_SETTINGS_BOT), state="*")


async def main():
    # Регистрация хэндлеров
    register_handlers_common(dp)
    register_handlers_main(dp)

    # Запуск поллинга
    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())
