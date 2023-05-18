from aiogram import types
from aiogram.dispatcher import FSMContext

from commands import Commands
from trc20.transactions import getTransactionsByAccount


async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [Commands.START_BOT, Commands.PAUSE_BOT, Commands.PAUSE_BOT]
    keyboard.add(*buttons)


    await message.answer(
        'Hello, my friend.\n I am help to you free time and make more money.\nFor start click <b>"Start make money"</b>',
        parse_mode=types.ParseMode.HTML,
        reply_markup=keyboard
    )
