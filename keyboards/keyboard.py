from aiogram import types


def get_keyboard(answers, sub):
    buttons = [types.InlineKeyboardButton(text=a[0], callback_data=sub + str(a[1])) for a in answers]
    # Генерация клавиатуры.
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    return keyboard