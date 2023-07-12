import string

from aiogram import types
from cryptography.fernet import Fernet
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

from config.botConfig import dp, config
from database.query import create_user, checkTrById, checkTrByUserIdAndTrId, updateDeposit, \
    updateLoss, \
    update_api_key, update_api_secret, update_user_is_blocked, getAmountByUserTr, update_user_tr_id, \
    update_user_is_active, \
    updateProfit, get_user_salt_by_id, get_bot_plans
from keyboards.keyboard import get_keyboard
from utils.trc20_transactions import getTransactionsByAccount

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
    # TODO Find user in VIP Chat

    message_pay = "Ok. I am find you in VIP chat.\nFor start get more time and money, select payment plan"
    pay_plans = get_bot_plans(config)
    await message.answer(message_pay,
                         reply_markup=get_keyboard(pay_plans, "plan_"),
                         parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(Text(startswith="plan_"))
async def callbacks_select_pay(call: types.CallbackQuery):
    # Парсим строку и извлекаем действие, например `ans_1` -> `ans_0`
    action = int(call.data.split("_")[1])

    wallet = "TS2xuQQn5iip2knVXfYzksw5CatN3WsQku"
    create_user(config, call.from_user.id, action)

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
    tr_id = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    found = False
    if len(tr_id) != 64:
        await message.answer("Please, write correct Transaction number")
        await state.finish()
        await Paying.transaction.set()
    else:
        # Check tr in database
        tr_id_db = checkTrById(config, tr_id)
        if tr_id_db[0] == 0:
            found = await check_transaction(message)
        else:
            # Tr already found and check in database by user
            tr_id_db = checkTrByUserIdAndTrId(config, message.from_user.id, tr_id)
            if tr_id_db[0] == 0:
                update_user_is_blocked(config, message.from_user.id)
                await message.answer("%s" % blocking_message)
            else:
                found = True

        if found:
            await state.finish()
            await message.answer("All is Great!\n" +
                                 "Go to the https://www.bybit.com/app/user/api-management\n\n<b>And create api key by instructions\n" +
                                 "https://docs.google.com/document/d/1ke_gkzCjq68uoz5cUQbL1IT_UkRcirGY6zPv3sm1AM8/edit?usp=sharing</b>",
                                 parse_mode=types.ParseMode.HTML)
            await message.answer("Send to me Api_Key")
            await ApiKeys.api_key.set()


async def check_transaction(message):
    transaction_id = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    user_id = message.from_user.id
    # Check tr by database
    limit = 10
    found = False
    transactions = getTransactionsByAccount("TS2xuQQn5iip2knVXfYzksw5CatN3WsQku", limit)
    print("Checking TRANSACTION.......................")
    await message.answer(transactions["data"])
    for transaction in transactions["data"]:
        if transaction["transaction_id"] == transaction_id:
            print(transaction)
            amount = int(int(transaction["value"])/1000000)
            print("amount = ", amount)
            # Get amount by user
            amount_db = getAmountByUserTr(config, user_id, transaction_id)
            is_diff_amount = amount != amount_db
            # If amount diff, then blocked
            if is_diff_amount:
                update_user_is_blocked(config, user_id)
                await message.answer("%s" % blocking_message)
            else:
                found = True
                # Add to Database tr_id
                update_user_tr_id(config, user_id, transaction_id)
        limit += 10
    return found


@dp.callback_query_handler(Text(startswith="sett_"))
async def callbacks_settings_bot(call: types.CallbackQuery):
    await start_settings(call.message)

    # Не забываем отчитаться о получении колбэка
    await call.answer()


@dp.message_handler(state=Paying.deposit)
async def callbacks_select_pay(message: types.Message, state: FSMContext):
    deposit = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    deposit.replace("%", "")
    if not(deposit.isdigit()) or len(deposit) == 0 or len(deposit) > 2:
        await message.answer('''You are input <b>not correct Deposit</b>. Try again.
        \nHow much you want to trade deposit for one deal? (1-50%)
        \nWe recommended using 3-5% by deposit''', parse_mode=types.ParseMode.HTML)
        await state.finish()
        await Paying.deposit.set()
    else:
        # Не забываем отчитаться о получении колбэка
        await state.finish()
        updateDeposit(config, message.from_user.id, deposit)
        await message.answer("How much you want to use StopLoss? (0-100%)")
        await Paying.stop_loss.set()


@dp.message_handler(state=Paying.stop_loss)
async def callbacks_set_stop(message: types.Message, state: FSMContext):
    stop_loss = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    stop_loss.replace("%", "")

    if not(stop_loss.isdigit()) or (len(stop_loss) == 0 or len(stop_loss) > 2):
        await message.answer('''You are input <b>not correct StopLoss</b>. Try again.
                \nHow much you want to use StopLoss? (0-100%)''', parse_mode=types.ParseMode.HTML)
        await state.finish()
        await Paying.stop_loss.set()
    else:
        # Не забываем отчитаться о получении колбэка
        await state.finish()
        updateLoss(config, message.from_user.id, stop_loss)
        await message.answer("How much you want to use TakeProfit? (0-100%)")
        await Paying.take_profit.set()


@dp.message_handler(state=Paying.take_profit)
async def callbacks_set_profit(message: types.Message, state: FSMContext):
    take_profit = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    take_profit.replace("%", "")

    if not(take_profit.isdigit()) or (len(take_profit) == 0 or len(take_profit) > 2):
        await message.answer('''You are input <b>not correct TakeProfit<b>. Try again.
                \nHow much you want to use StopLoss? (0-100%)''', parse_mode=types.ParseMode.HTML)
        await state.finish()
        await Paying.take_profit.set()
    else:
        # Не забываем отчитаться о получении колбэка
        await state.finish()
        updateProfit(config, message.from_user.id, take_profit)
        await message.answer("Ok. I am working :-)")


@dp.message_handler(state=ApiKeys.api_key)
async def callbacks_set_api_key(message: types.Message, state: FSMContext):
    api_key = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    if len(api_key) != 18:
        await message.answer("Please, input correct Bybit <b>Api Key</b>", parse_mode=types.ParseMode.HTML)
        await state.finish()
        await ApiKeys.api_key.set()
    else:
        await state.finish()
        salt = Fernet.generate_key()
        cipher = Fernet(salt)
        update_api_key(config, message.from_user.id, salt, cipher.encrypt(bytes(api_key, 'utf-8')))
        await message.answer("Send to me Api Key Secret")
        await ApiKeys.api_secret.set()


@dp.message_handler(state=ApiKeys.api_secret)
async def callbacks_set_api_secret(message: types.Message, state: FSMContext):
    api_secret = message.text.lower().translate(str.maketrans('', '', string.punctuation))
    if len(api_secret) != 36:
        await message.answer("Please, input correct Bybit <b>Api Secret</b>", parse_mode=types.ParseMode.HTML)
        await state.finish()
        await ApiKeys.api_secret.set()
    else:
        await state.finish()
        user_salt = get_user_salt_by_id(config, message.chat.id)
        cipher = Fernet(user_salt[0])
        update_api_secret(config, message.from_user.id, user_salt[0], cipher.encrypt(bytes(api_secret, 'utf-8')))
        await message.answer("Thank you for create Api Keys!",
                             reply_markup=get_keyboard([["Start to set settings (After that bot will be start)", True]],
                                                       "sett_"))


async def cmd_pause_bot(message: types.Message):
    # Check to have db user AND
    # Set isActive = False
    update_user_is_active(config, message.from_user.id, False)
    await message.answer("Ok. I did stop my work" +
                         "\nI will hope you come back to me",
                         parse_mode=types.ParseMode.HTML)


async def cmd_edit_settings(message: types.Message):
    await start_settings(message)


async def start_settings(message: types.Message):
    await message.answer(
        "How much you want to trade <b>deposit for one deal?</b> (1-50%) \nWe recommended using 3-5% by deposit",
        parse_mode=types.ParseMode.HTML)
    await Paying.deposit.set()
