from datetime import datetime as dt

import requests as req
import json

endpoint = 'https://api.bitflyer.jp/v1/'
api_key = {
    'history': 'executions',
    'board': 'board',
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


def api(api_name: str, payloads=None):
    res = req.get(endpoint + api_key[api_name], params=payloads)
    return json.loads(res.text)


def dumps(dic: dict, order: list):
    s = []
    for key in order:
        s.append(str(dic[key]))
    return ','.join(s)


def date2str(dateobj: dt):
    return dateobj.strftime(time_format)


def str2date(tstr):
    # tstr = '2015-07-08T02:43:34.72'
    tdatetime = dt.strptime(tstr, time_format)
    return tdatetime