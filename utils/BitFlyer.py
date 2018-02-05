# coding: UTF-8

import os
import requests as req
import json
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

api_key = os.getenv('BF_KEY', '-')
api_secret = os.getenv('BF_SECRET', '-')
api_pb = pybitflyer.API(api_key=api_key, api_secret=api_secret)


def api(api_name: str, payloads=None):
    if api_name in api_dict:
        api_name = api_dict[api_name]
    res = req.get(endpoint + api_name, params=payloads)
    try:
        return json.loads(res.text)
    except json.JSONDecodeError as e:
        logger.exception(e)
        return None


def api_me(api_method, http_method='GET', body=None):
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
