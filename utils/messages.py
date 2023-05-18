from config.botConfig import bot
from userData import User, UserKeys


async def del_message(message):
    await bot.delete_message(message.chat.id, User.user_data[message.chat.id][UserKeys.SCORE_MESS_ID])
    await bot.delete_message(message.chat.id, User.user_data[message.chat.id][UserKeys.SCORE_MESS_ID] + 1)


async def getChatId(call):
    return call.message.chat.id
