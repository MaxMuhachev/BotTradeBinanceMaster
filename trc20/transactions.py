import requests
from aiogram.utils import json


def getTransactionsByAccount(address, lmit):
    url = f'https://api.trongrid.io/v1/accounts/{address}/transactions/trc20?'
    payload = {
        "sort": 'blockNumber',
        "search_internal": "false",
        "limit": lmit,
        "only_to": "true",
        "only_confirmed": "true"
    }
    res = requests.get(url, params=payload)
    obj = json.loads(res.text)
    return obj
