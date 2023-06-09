from mysql import connector


def initDbConnection(config):
    context = connector.connect(
        host=config["Database"]["host"],
        port=config["Database"]["port"],
        user=config["Database"]["username"],
        password=config["Database"]["password"],
        database=config["Database"]["database"])
    return context


def closeConn(context):
    # Разрываем подключение.
    context.close()
