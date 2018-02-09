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


def _trade(param={}):
    new_param = {
        'pair': param.get('pair', 'btc_jpy'),
        'limit': param.get('count', 100),
    }
    data = json.loads(cc.trade.all(new_param))
    result = []
    for d in data['data']:
        result.append({
            'id': int(d['id']),
            'side': d['order_type'].upper(),
            'price': float(d['rate']),
            'size': float(d['amount']),
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
            "amount": float(data['jpy']) + float(data['jpy_reserved']),
            "available": float(data['jpy'])
        },
        {
            "currency_code": "BTC",
            "amount": float(data['btc']) + float(data['btc_reserved']),
            "available": float(data['btc'])
        }
    ]
    return result


def _order(param: dict):
    body = {
        'rate': param['price'],
        'amount': param['size'],
        'pair': param['product_code'].lower(),
        'order_type': param['side'].lower(),
    }
    if param.get('child_order_type', '') == 'MARKET':
        if body['order_type'] == 'buy':
            body['market_buy_amount'] = int(body['rate'] * body['amount'])
        body['order_type'] = 'market_' + body['order_type']
    data = json.loads(cc.order.create(body))
    data['child_order_acceptance_id'] = 'coincheck-order'
    return data


api_func = {
    'ticker': _ticker,
    'history': _trade,
    'getbalance': _balance,
    'sendchildorder': _order,
}


def api(api_name: str, payloads=None):
    try:
        return api_func[api_name]()
    except json.JSONDecodeError as e:
        logger.exception(e)
        return None


def api_me(api_method, http_method='GET', body=None):
    try:
        return api_func[api_method](body)
    except json.JSONDecodeError as e:
        logger.exception(e)
        return None


def _order_list():
    data = json.loads(cc.order.opens())
    opens = []
    for order in data['orders']:
        opens.append(int(order['id']))
    return opens


def cancel_all():
    try:
        for oid in _order_list():
            data = json.loads(cc.order.cancel({'id': oid}))
            logger.info('cancel: %s' % data)
            time.sleep(1)
    except json.JSONDecodeError as e:
        logger.exception(e)
