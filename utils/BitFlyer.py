from datetime import datetime as dt

import os
import requests as req
import json
import time
import hmac
import hashlib
from utils.settings import get_logger
import pybitflyer

logger = get_logger()


endpoint = 'https://api.bitflyer.jp/v1/'
api_dict = {
    'history': 'executions',
    'board': 'board',
    'ticker': 'ticker',
}

execution_keys = [
    "id",# : 37233,
    "side",# : "BUY",
    "price",# : 33470,
    "size",# : 0.01,
    # "commission",# : 0,
    "exec_date",# : "2015-07-07T09:57:40.397",
    # "child_order_id",# : "JOR20150707-060559-021935",
    # "child_order_acceptance_id",# : "JRF20150707-060559-396699"
]

time_format = '%Y-%m-%dT%H:%M:%S.%f'
time_format_nf = '%Y-%m-%dT%H:%M:%S.%f'

api_key = os.getenv('BF_KEY', '-')
api_secret = os.getenv('BF_SECRET', '-')
api_pb = pybitflyer.API(api_key=api_key, api_secret=api_secret)


def api(api_name: str, payloads=None):
    res = req.get(endpoint + api_dict[api_name], params=payloads)
    try:
        return json.loads(res.text)
    except json.JSONDecodeError as e:
        logger.exception(e)
        return None


def api_me(api_method, http_method='GET', body=None):
    # timestamp = str(int(time.time() * 1000))
    # text = timestamp + http_method + '/v1/me/' + api_method
    # if body:
    #     text += json.dumps(body)
    # sign = hmac.new(bytearray(api_secret, 'utf-8'), bytearray(text, 'utf-8'), hashlib.sha256).hexdigest()
    # headers = {
    #     'ACCESS-KEY': api_key,
    #     'ACCESS-TIMESTAMP': timestamp,
    #     'ACCESS-SIGN': sign,
    #     'Content-Type': 'application/json'
    # }
    # if http_method == 'GET':
    #     func = req.get
    # elif http_method == 'POST':
    #     func = req.post
    # else:
    #     return None
    # res = func(endpoint + 'me/' + api_method, headers=headers, params=body)
    try:
        return api_pb.request('/v1/me/' + api_method, method=http_method, params=body)
    except json.JSONDecodeError as e:
        logger.exception(e)
        return None


def dumps(dic: dict, order: list):
    s = []
    for key in order:
        s.append(str(dic[key]))
    return ','.join(s)


def date2str(dateobj: dt):
    return dateobj.strftime(time_format)


def str2date(tstr):
    # tstr = '2015-07-08T02:43:34.72'
    format = time_format if '.' in tstr else tstr
    tdatetime = dt.strptime(tstr, format)
    return tdatetime
