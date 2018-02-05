# coding: UTF-8
from datetime import datetime as dt

import os
import requests as req
import json
import time
import hmac
import hashlib
from utils.settings import get_logger
from coincheck.coincheck import CoinCheck

logger = get_logger()


api_key = os.getenv('CC_KEY', '-')
api_secret = os.getenv('CC_SECRET', '-')
cc = CoinCheck(api_key, api_secret)


def _ticker():
    data = json.loads(cc.ticker.all())
    data['best_bid'] = data['bid']
    data['best_ask'] = data['ask']
    return data


def _trade(param=None):
    if param is None:
        param = {'pair': 'btc_jpy'}
    data = json.loads(cc.trade.all(param))
    result = []
    for d in data['data']:
        result.append({
            'id': d['id'],
            'side': d['order_type'].upper(),
            'price': d['rate'],
            'size': d['amount'],
            'exec_date': d['created_at'][:-1],
            'buy_child_order_acceptance_id': '-',
            'sell_child_order_acceptance_id': '-',
        })
    return result


def _balance(param):
    data = json.loads(cc.account.balance())
    result = [
        {
            "currency_code": "JPY",
            "amount": data['jpy'] + data['jpy_reserved'],
            "available": data['jpy']
        },
        {
            "currency_code": "BTC",
            "amount": data['btc'] + data['btc_reserved'],
            "available": data['btc']
        }
    ]
    return result


def _order(param):
    body = {
        'rate': param['price'],
        'amount': param['size'],
        'pair': param['product_code'].lower(),
        'order_type': param['side'].lower(),
    }
    data = json.loads(cc.order.create(body))
    data['child_order_acceptance_id'] = '-'
    return [data]


api_func = {
    'ticker': _ticker,
    'history': _trade,
    'getbalance': _balance,
}


def api(api_name: str, payloads=None):
    return api_func[api_name]()


def api_me(api_method, http_method='GET', body=None):
    return api_func[api_method](body)
