import string
from contextlib import suppress

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import MessageNotModified

from config.botConfig import dp, config, bot
from database.query import getQuestionBySection, createUser, checkTrById, checkTrByUserIdAndTrId, updateDeposit, \
    updateLoss, \
    updateApiKey, updateApiSecret, update_user_is_blocked, getAmountByUserTr, update_user_tr_id
from keyboards.keyboard import get_keyboard
from trc20.transactions import getTransactionsByAccount
from userData import User, UserKeys
from utils.messages import getChatId

blocking_message = "Your account is suspected of fraud and has been blocked. Contact administrator"


class Paying(StatesGroup):
    transaction = State()
    deposit = State()
    stop_loss = State()
    take_profit = State()


class ApiKeys(StatesGroup):
    api_key = State()
    api_secret = State()


async def cmd_start(message: types.Message):
    user_map_value = User.user_data.get(message.chat.id, 0)
    if user_map_value == 0:
        # TODO Find user in VIP Chat

        message_pay = "Ok. I am find you in VIP chat.\nFor start get more time and money, select payment plan"

        # price = await getQuestionBySection(config, number_question)
        # TODO LATER  Get price prom database?

        pay_plan = [["$30 every mounth", 30], ["$300 Lifetime", 300]]
        await message.answer(message_pay,
                             reply_markup=get_keyboard(pay_plan, "plan_"),
                             parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(Text(startswith="plan_"))
async def callbacks_select_pay(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    # Парсим строку и извлекаем действие, например `ans_1` -> `ans_0`
    action = int(call.data.split("_")[1])

    wallet = "XXXXXXX"
    createUser(config, call.from_user.id, chat_id, action)

    await call.message.edit_text(f"Ok. Pay to me {str(action)}$ on the wallet {wallet}",
                                 reply_markup=get_keyboard([["Ok. I paid", action]], "pay_"))
    # Не забываем отчитаться о получении колбэка
    await call.answer()


@dp.callback_query_handler(Text(startswith="pay_"))
async def callbacks_select_pay(call: types.CallbackQuery):
    await call.message.edit_text("Ok. Send to me transaction number Only Confirmed. I will verify it", parse_mode=types.ParseMode.HTML)
    await Paying.transaction.set()

    # Не забываем отчитаться о получении колбэка
    await call.answer()


# ee8476f99c15cfa8826b556d074b7272406773cc15e33125d5c17149915c04fe
@dp.message_handler(state=Paying.transaction)
async def callbacks_check_transaction(message: types.Message, state: FSMContext):
    trId = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    found = False
    if len(trId) != 64:
        await message.answer("Please, write correct Transaction number")
        await state.finish()
        await Paying.transaction.set()

    tr_id_db = checkTrById(config, trId)
    if tr_id_db is None:
        found = await check_transaction(message)
    else:
        tr_id_db = checkTrByUserIdAndTrId(config, message.from_user.id, trId)
        if tr_id_db is None:
            await message.answer("Your transaction not found", parse_mode=types.ParseMode.HTML)
        else:
            found = await check_transaction(message)

    if found:
        await state.finish()
        await message.answer("All is Great!\n" +
                             "Go to the https://www.bybit.com/app/user/api-management\n\n<b>And create api key by instructions\n" +
                             "https://docs.google.com/document/d/1ke_gkzCjq68uoz5cUQbL1IT_UkRcirGY6zPv3sm1AM8/edit?usp=sharing</b>",
                             parse_mode=types.ParseMode.HTML)
        await message.answer("Please, send me Api_Key")
        await ApiKeys.api_key.set()


async def check_transaction(message):
    transaction_id = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    user_id = message.from_user.id
    # Check tr by database
    found_tr_db = checkTrById(message.from_user.id, transaction_id)
    if found_tr_db:
        update_user_is_blocked(config, user_id)
        await message.answer("%s" % blocking_message)
    else:
        limit = 10
        found = False
        while not found:
            transactions = getTransactionsByAccount("TGgkWaenzuwY7EXbMxWtcHwhnMgem8jGgU", limit)
            print("Checking TRANSACTION.......................")
            for transaction in transactions["data"]:
                if transaction["transaction_id"] == transaction_id:
                    print(transaction)
                    amount = int(int(transaction["value"])/1000000)
                    print("amount = ", amount)
                    # Get amount by user
                    amount_db = getAmountByUserTr(config, user_id, transaction_id)
                    is_diff_amount = amount_db != amount
                    # If amount diff, then blocked
                    if is_diff_amount:
                        update_user_is_blocked(config, user_id)
                        await message.answer("%s" % blocking_message)
                    found = True
                    # Add to Database tr_id
                    update_user_tr_id(config, user_id, transaction_id)
                break
            limit += 10
    return True


@dp.callback_query_handler(Text(startswith="sett_"))
async def callbacks_settings_bot(call: types.CallbackQuery):
    await set_settings_bot(call.message)

    # Не забываем отчитаться о получении колбэка
    await call.answer()


@dp.message_handler(state=Paying.deposit)
async def callbacks_select_pay(message: types.Message, state: FSMContext):
    deposit = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    deposit.replace("%", "")
    if (len(deposit) == 0 or len(deposit) > 2):
        await message.edit_text('''<b>You are input not right <b>Deposit</b>. Try again.<b>
        \nHow much you want to trade deposit for one deal? (1-50%)
        \nWe recommended using 3-5% by deposit''', parse_mode=types.ParseMode.HTML)
        await state.finish()
        await Paying.deposit.set()
    else:
        # Не забываем отчитаться о получении колбэка
        await state.finish()
        updateDeposit(config, message.from_user.id, deposit)


@dp.message_handler(state=Paying.stop_loss)
async def callbacks_set_stop(message: types.Message, state: FSMContext):
    stop_loss = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    stop_loss.replace("%", "")

    if (len(stop_loss) == 0 or len(stop_loss) > 2):
        await message.edit_text('''<b>You are input not right <b>StopLoss</b>. Try again.<b>
                \nHow much you want to use StopLoss? (0-100%)''', parse_mode=types.ParseMode.HTML)
        await state.finish()
        await Paying.deposit.set()
    else:
        # Не забываем отчитаться о получении колбэка
        await state.finish()
        updateLoss(config, message.from_user.id, stop_loss)


@dp.message_handler(state=Paying.take_profit)
async def callbacks_set_profit(message: types.Message, state: FSMContext):
    take_profit = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    take_profit.replace("%", "")

    if (len(take_profit) == 0 or len(take_profit) > 2):
        await message.edit_text('''<b>You are input not right <b>TakeProfit</b>. Try again.<b>
                \nHow much you want to use StopLoss? (0-100%)''', parse_mode=types.ParseMode.HTML)
        await state.finish()
        await Paying.deposit.set()
    else:
        # Не забываем отчитаться о получении колбэка
        await state.finish()
        updateLoss(config, message.from_user.id, take_profit)


@dp.message_handler(state=ApiKeys.api_key)
async def callbacks_set_api_key(message: types.Message, state: FSMContext):
    api_key = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    if len(api_key) != 18:
        await message.answer("Please, input correct Bybit <b>Api Key</b>", parse_mode=types.ParseMode.HTML)
        await state.finish()
        await ApiKeys.api_key.set()
    else:
        await state.finish()
        updateApiKey(config, message.from_user.id, api_key)


@dp.message_handler(state=ApiKeys.api_secret)
async def callbacks_set_api_secret(message: types.Message, state: FSMContext):
    api_secret = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    if len(api_secret) != 36:
        await message.answer("Please, input correct Bybit <b>Api Secret</b>", parse_mode=types.ParseMode.HTML)
        await state.finish()
        await ApiKeys.api_key.set()
    else:
        await state.finish()
        updateApiSecret(config, message.from_user.id, api_secret)
        await message.answer("Thank you for create Api Keys!",
                             reply_markup=get_keyboard([["Start to set settings (After that bot will be start)", True]],
                                                       "sett_"))


async def cmd_pause_bot(message: types.Message):
    # Check to have db user AND
    # Set isActive = False
    update_user_is_active()
    await message.answer("Ok. I did stop my work" +
                         "\nI will hope you come back to me",
                         parse_mode=types.ParseMode.HTML)


async def cmd_edit_settings(message: types.Message):
    await set_settings_bot(message)


async def cmd_cancel(message: types.Message):
    await message.answer("Последний ответ был <b>" + User.user_data[message.chat.id][UserKeys.LAST_RESULT] +
                         "</b>\nСпасибо за игру. Вы набрали <b>" +
                         str(User.user_data[message.chat.id][UserKeys.SCORE]) + " очков</b>." +
                         "\nВ следующий раз вам повезёт больше &#128521;",
                         parse_mode=types.ParseMode.HTML)
    User.user_data.pop(message.chat.id)


# async def update_ques_text(message: types.Message):
#     with suppress(MessageNotModified):
#         User.user_data[message.chat.id][UserKeys.SECTION] += 1
#
#         await bot.edit_message_text(
#             text="<b>Ответ " + User.user_data[message.chat.id][UserKeys.LAST_RESULT] +
#                  "</b> Текущее количество очков: <b>" +
#                  str(User.user_data[message.chat.id][UserKeys.SCORE]) + "</b>",
#             chat_id=message.chat.id,
#             message_id=User.user_data[message.chat.id][UserKeys.SCORE_MESS_ID],
#             parse_mode=types.ParseMode.HTML)
#
#         number_question = User.user_data[message.chat.id][UserKeys.SECTION]
#         questions = await getQuestionBySection(config, number_question)
#         if len(questions) > 0:
#             await message.edit_text(str(number_question) + ". " + questions[0][0] + "?",
#                                     reply_markup=get_keyboard(questions, message.chat.id))
#         else:
#             await cmd_pause_bot(message)


async def set_settings_bot(message: types.Message):
    await message.answer(
        "How much you want to trade deposit for one deal? (1-50%) \nWe recommended using 3-5% by deposit")
    await Paying.deposit.set()

    await message.answer("How much you want to use StopLoss? (0-100%)")
    await Paying.stop_loss.set()

    await message.answer("How much you want to use TakeProfit? (0-100%)")
    await Paying.take_profit.set()

    await message.answer("Ok. I am working :-)")
