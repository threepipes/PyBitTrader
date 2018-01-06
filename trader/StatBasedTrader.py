import time
import pandas as pd
from logging import getLogger, basicConfig, DEBUG, WARN
import json

import Functions as F
from VirtualApi import VirtualApi
from database.TradeHistory import Border, Order, get_session

logger = getLogger(__file__)


class Trader:
    def __init__(self):
        self.last_start = 0
        self.data_range = 500
        self.std_coef = 1.75
        self.least_trade_limit = 0.01
        self.commission = 0.15 / 100
        self.interval_sec = 10
        self.session = get_session()
        self.pre_sell_price = 99999999
        self.pre_buy_price = 0
        self.last_trade = 0

        self.debug = VirtualApi()

    def _update(self):
        # interval_sec秒ごとに実行
        self.last_start = time.time()
        res, me = self.get_recent_data()
        sell_line, buy_line = self._set_trade_line(res)
        order = self._generate_order(me, sell_line, buy_line)
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
        # 最新100件の取引履歴
        # res = pd.DataFrame(F.api('history'))
        res = None
        # 資産状況
        me = self.debug.api_me('getbalance')
        me = pd.DataFrame(me).set_index('currency_code')
        return res, me

    def _set_trade_line(self, recent):
        # 過去のデータから，売買ラインを見極める
        # mean = recent.price.mean()
        # std = recent.price.std()
        # sell_line = mean + std * self.std_coef
        # buy_line = mean - std * self.std_coef
        buy_line = int(self.pre_sell_price * (1 - 0.05))
        sell_line = int(self.pre_buy_price * 1.02 + 1)
        return sell_line, buy_line

    def _generate_order(self, me, sell_line, buy_line):
        # 注文を生成する
        ticker = F.api('ticker')
        mid_val = (ticker['best_bid'] + ticker['best_ask']) // 2
        jpy = me.loc['JPY'].available
        btc = me.loc['BTC'].available
        jpy_btc_val = jpy / mid_val

        logger.debug('trade line: sell=%f buy=%f price=%d',
                     sell_line, buy_line, mid_val)

        border_data = Border.create(mid_val, buy_line, sell_line)
        self.session.add(border_data)

        order = {
            'product_code': 'BTC_JPY',
            'child_order_type': 'LIMIT',
            'price': int(mid_val),
            'minute_to_expire': 1,
        }

        passed = time.time() - self.last_trade
        if jpy_btc_val > self.least_trade_limit\
                and (mid_val < buy_line
                     or passed > 60 * 60 * 24 * 5):
            order['size'] = jpy / (mid_val * (1 + self.commission))
            order['side'] = 'BUY'
            self.pre_buy_price = mid_val
        elif btc > self.least_trade_limit\
                and (mid_val > sell_line
                     or passed > 60 * 60 * 24 * 5):
            order['size'] = btc * (1 - self.commission)
            order['side'] = 'SELL'
            self.pre_sell_price = mid_val
        else:
            return None
        self.last_trade = time.time()
        logger.debug('pre_buy=%d pre_sell=%d passed=%f',
                     self.pre_buy_price, self.pre_sell_price, passed)
        logger.info('ORDER: %s    [price: %d]', json.dumps(order), mid_val)
        logger.debug('me: jpy=%s btc=%s', str(jpy), str(btc))
        return order


def logging_config():
    basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                level=DEBUG)
    requests_logger = getLogger('requests.packages.urllib3')
    requests_logger.setLevel(WARN)


def run():
    logging_config()
    trader = Trader()
    trader.run()
