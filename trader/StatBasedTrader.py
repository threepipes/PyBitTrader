import time
import pandas as pd
import json
from sqlalchemy.sql.expression import func
import datetime

import Functions as F
from utils.settings import logging_config, get_logger
from VirtualApi import VirtualApi
from database.TradeHistory import Order, History, get_session
from database.db_utils import get_recent_hist_df, history2indicator
from model.model_utils import load_agent

logger = get_logger().getChild(__file__)


class State:
    UNIT_MAX = 4

    def __init__(self):
        self.unit = 0

    def trade(self, price, price_pre, action):
        diff = abs(action - self.unit)
        coef = diff / max(action, self.unit)
        reward = self.unit * (price / price_pre - 1)
        self.unit = action
        return coef, reward


class Trader:
    def __init__(self):
        self.last_start = 0
        self.least_trade_limit = 0.01
        self.commission = 0.15 / 100
        self.interval_sec = 60 * 15
        self.session = get_session()
        self.last_trade = 0

        self.action_hist = {
            'r': 0,
            'r_1': 0,
            'r_2': 0,
            'state': 0
        }
        self.agent = load_agent()
        self.state = State()

        self.debug = VirtualApi()

    def _update(self):
        # interval_sec秒ごとに実行
        self.last_start = time.time()
        res, me = self.get_recent_data()
        action, price, price_pre = self._decide_action(res)
        order = self._generate_order(me, action, price, price_pre)
        if order:
            order_id = self.debug.api_me('sendchildorder', 'POST', body=order)
            order_data = Order.create(order, order_id)
            self.session.add(order_data)
            # logger.info('order id: %s, ', json.dumps(order_id))
        self.session.commit()

    def run(self):
        logger.info('starting trader')
        while True:
            try:
                wait = max(0, self.interval_sec - (time.time() - self.last_start))
                time.sleep(wait)
                self._update()
            except Exception as e:
                logger.error(e)
            time.sleep(10)

    def get_recent_data(self):
        # logger.debug('getting recent data')
        # self._add_history()  # DataMiningを並行して動かすこととする(必須)
        # 最新1週間の取引履歴
        week_ago = datetime.datetime.utcnow() - datetime.timedelta(weeks=2, hours=1)
        res = get_recent_hist_df(week_ago, self.session)
        # 資産状況
        me = self.debug.api_me('getbalance')
        me = pd.DataFrame(me).set_index('currency_code')
        return res, me

    def _add_history(self):
        pre_hist_id, = self.session.query(func.max(History.id)).first()
        hist = F.api('history', payloads={'after': pre_hist_id, 'count': 500})
        for h in hist:
            h['exec_date'] = F.str2date(h['exec_date'])
            hist_data = History(**h)
            self.session.add(hist_data)
        self.session.commit()

    def _decide_action(self, recent):
        # 過去のデータから行動決定
        indicator, price, price_pre = history2indicator(recent, **self.action_hist)
        return self.agent.act(indicator), price, price_pre

    def _generate_order(self, me, action, price_15, price_15_pre):
        # 注文を生成する
        ticker = F.api('ticker')
        mid_val = (ticker['best_bid'] + ticker['best_ask']) // 2
        jpy = me.loc['JPY'].available
        btc = me.loc['BTC'].available

        logger.debug('trade act: act=%d price=%d resource=%f', action, mid_val, jpy + btc * mid_val)

        order = {
            'product_code': 'BTC_JPY',
            'child_order_type': 'LIMIT',
            'price': int(mid_val),
            'minute_to_expire': 10,
        }

        coef, reward = self.state.trade(price_15, price_15_pre, action)
        act_pre = self.action_hist['state']

        self.action_hist = {
            'r': reward,
            'r_1': self.action_hist['r'],
            'r_2': self.action_hist['r_1'],
            'state': action
        }

        if act_pre < action:
            order['size'] = jpy * coef / (mid_val * (1 + self.commission))
            order['side'] = 'BUY'
        elif act_pre > action:
            order['size'] = btc * coef * (1 - self.commission)
            order['side'] = 'SELL'
        else:
            return None
        self.last_trade = time.time()
        logger.info('ORDER: %s    [price: %d]', json.dumps(order), mid_val)
        logger.debug('me: jpy=%s btc=%s', str(jpy), str(btc))

        return order


def run():
    logging_config()
    trader = Trader()
    trader.run()
