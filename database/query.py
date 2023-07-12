import logging

from pymysql import Error

from database.connect import initDbConnection, closeConn


def get_expired_users(config):
    query = "SELECT user_id FROM users WHERE date_api_create <= DATE_SUB(CURRENT_DATE, INTERVAL 89 DAY);"
    return fetch_all(config, query)


def get_bot_plans(config):
    query = "SELECT '$', CONCAT(price, '$ ', message_per), price FROM bot_plan"
    return fetch_all(config, query)


def get_user_salt_by_id(config, user_id):
    query = f"SELECT salt FROM users WHERE user_id = {user_id};"
    return fetch_one(config, query)


def checkTrById(config, tr_id):
    query = f"SELECT count(*) FROM users WHERE tr_id = '{str(tr_id)}'"
    return fetch_one(config, query)


def checkTrByUserIdAndTrId(config, user_id, tr_id):
    query = f"SELECT count(*) FROM users WHERE user_id = {user_id} AND tr_id = '{str(tr_id)}'"
    return fetch_one(config, query)


def getAmountByUserTr(config, user_id, tr_id):
    query = f"SELECT bp.price FROM users u JOIN bot_plan bp on u.plan_id = bp.id WHERE u.user_id = {user_id} AND u.tr_id = '{str(tr_id)}'"
    return fetch_one(config, query)


def updateDeposit(config, user_id, deposit):
    query = f"UPDATE users SET deposit = {int(deposit)} WHERE user_id = {user_id}"
    return execute_query(config, query)


def updateLoss(config, user_id, stop_loss):
    query = f"UPDATE users SET stop_loss = {int(stop_loss)} WHERE user_id = {user_id}"
    return execute_query(config, query)


def updateProfit(config, user_id, take_profit):
    query = f"UPDATE users SET take_profit = {int(take_profit)} AND is_active = true WHERE user_id = {user_id}"
    return execute_query(config, query)


def update_api_key(config, user_id, salt, api_key):
    query = f"UPDATE users SET bybit_api_key = '{str(api_key)}' AND salt = '{str(salt)}'  WHERE user_id = {user_id}"
    return execute_query(config, query)


def update_api_secret(config, user_id, salt, api_secret):
    query = f"UPDATE users SET bybit_api_secret = '{str(api_secret)}' AND salt = '{str(salt)}' AND date_api_create = now() WHERE user_id = {user_id}"
    return execute_query(config, query)


def update_user_is_blocked(config, user_id):
    query = f"UPDATE users SET is_blocked = true WHERE user_id = {user_id}"
    return execute_query(config, query)


def update_user_tr_id(config, user_id, tr_id):
    query = f"UPDATE users SET tr_id = '{tr_id}' WHERE user_id = {user_id}"
    return execute_query(config, query)


def update_user_is_active(config, user_id, state: bool):
    query = f"UPDATE IGNORE users SET is_active = {state} WHERE user_id = {user_id}"
    return execute_query(config, query)


def create_user(config, user_id, plan):
    query = f"INSERT IGNORE INTO users(user_id, plan_id) VALUES  ({str(user_id)}, (SELECT id FROM bot_plan WHERE price ={str(plan)}))"
    execute_query(config, query)


def fetch_all(config, query):
    logging.info(query)
    context = initDbConnection(config)

    cursor = context.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    closeConn(context)
    return result


def fetch_one(config, query):
    logging.info(query)
    context = initDbConnection(config)

    cursor = context.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    closeConn(context)
    return result


def execute_query(config, query):
    logging.info(query)
    context = initDbConnection(config)
    cursor = context.cursor()
    try:
        cursor.execute(query)
        context.commit()
    except Error as err:
        context.rollback()
        print(err)
    finally:
        closeConn(context)
