# coding: UTF-8
import time
import pandas as pd
import json
from sqlalchemy.sql.expression import func
import datetime
import traceback
from requests.exceptions import ConnectionError

from utils import BitFlyer as F
from utils.settings import logging_config, get_logger
from utils.VirtualApi import VirtualApi
from database.TradeHistory import Order, History, get_session
from database.db_utils import (
    get_recent_hist_n_df, get_recent_hist_df,
    set_dateindex
)
from model.ChainerModel import history2indicator
from model.model_utils import load_predictor, predict_row
from ui.notification import slack
from DataMining import use_data_type, use_interval

logger = get_logger().getChild(__file__)


class Trader:
    def __init__(self):
        self.last_start = 0
        self.least_trade_limit = 0.01
        self.commission = 0  # 0.15 / 100
        self.interval_sec = 60 * use_interval
        self.session = get_session()
        self.last_trade = 0

        self.model = load_predictor()

        self.api = F  # VirtualApi()

    def _update(self):
        # interval_sec秒ごとに実行
        self.last_start = time.time()
        res, me = self.get_recent_data()
        action, price, price_pre = self._decide_action(res)
        for _ in range(3):
            order = self._generate_order(me, action)
            if not order:
                break
            order_id = self.api.api_me('sendchildorder', 'POST', body=order)
            logger.info('order id: %s, ', json.dumps(order_id))
            if 'child_order_acceptance_id' in order_id:
                order_data = Order.create(order, order_id['child_order_acceptance_id'])
                self.session.add(order_data)
                break
            if 'status' in order_id and order_id['status'] != -208:
                slack('Order error: \norder=%s\nresponse=%s' % (
                    json.dumps(order), json.dumps(order_id)
                ))
                logger.warn('Illegal order response.')
                break
            logger.warn('Order is not accepted. Retry.')
            time.sleep(5)
        self.session.commit()

    def run(self):
        logger.info('starting trader')
        while True:
            try:
                wait = max(0, self.interval_sec - (time.time() - self.last_start))
                time.sleep(wait)
                self._update()
            except ConnectionError as e:
                logger.exception(e)
            time.sleep(10)

    def get_recent_data(self):
        # logger.debug('getting recent data')
        # DataMiningを並行して動かすこととする(必須)
        # 最新1週間の取引履歴(15分足) -> 5分足に変更
        week_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=use_interval * 1000)
        res = get_recent_hist_n_df(week_ago, use_data_type, self.session)
        res = set_dateindex(res)

        latest = get_recent_hist_df(
            res.index[-1].to_pydatetime() + datetime.timedelta(minutes=use_interval),
            self.session)
        latest = set_dateindex(latest)
        l_price = latest.price.resample('%dMin' % use_interval).mean()
        l_size = latest['size'].resample('%dMin' % use_interval).sum().fillna(0)
        latest_df = pd.DataFrame([l_price, l_size]).T
        res = pd.concat([res, latest_df])

        logger.debug('latest mean: %f', l_price[l_price.index[-1]])

        # 資産状況
        me = self.api.api_me('getbalance')
        me = pd.DataFrame(me).set_index('currency_code')
        return res, me

    def _extract_market_size(self, df):
        # 直近の売買量を計算する
        pass

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
        indicator, price, price_pre = history2indicator(recent)
        return predict_row(self.model, indicator), price, price_pre

    def _generate_order(self, me, action, failed=False):
        # 注文を生成する
        ticker = F.api('ticker')
        if not ticker:
            logger.error('No ticker returned!')
            return None

        best_ask = ticker['best_ask']
        best_bid = ticker['best_bid']
        mid_val = (best_bid + best_ask) // 2
        jpy = me.loc['JPY'].available
        btc = me.loc['BTC'].available

        logger.debug('trade act: act=%d price=%d resource=%f (btc=%f, jpy=%f)',
                     action, mid_val, jpy + btc * mid_val, btc, jpy)

        order = {
            'product_code': 'BTC_JPY',
            'child_order_type': 'LIMIT',
            # 'child_order_type': 'MARKET',
            'price': int(mid_val),
            'minute_to_expire': use_interval - 1,
        }

        if action == 2 and jpy > 10000:
            p = best_ask
            order['size'] = (jpy - 1) / (p * (1 + self.commission))
            order['side'] = 'BUY'
        elif action == 0 and btc > 0.005:
            p = best_bid
            order['size'] = btc * (1 - self.commission)
            order['side'] = 'SELL'
        else:
            return None

        if failed:
            order['child_order_type'] = 'MARKET'
            del order['price']

        order['size'] = float('%.8f' % float(order['size']))
        self.last_trade = time.time()
        logger.info('ORDER: %s    [price: %d]', json.dumps(order), mid_val)
        logger.debug('me: jpy=%s btc=%s', str(jpy), str(btc))
        slack('order: side=%s mid_price=%d (jpy=%f + btc=%f -> %f) best_ask=%f best_bid=%f best_diff=%f' % (
            order['side'], int(mid_val), jpy, btc, jpy + btc * p,
            best_ask, best_bid, best_ask / best_bid - 1
        ))

        return order


def run():
    logging_config()
    trader = Trader()
    try:
        trader.run()
    except Exception as e:
        logger.exception(e)
        slack('Uncaught error occurred : %s' % traceback.format_exc())
