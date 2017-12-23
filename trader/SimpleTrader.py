import time
import pandas as pd
from logging import getLogger
import json

import Functions as F

logger = getLogger(__file__)


class Trader:
    def __init__(self):
        self.last_start = 0
        self.data_range = 200
        self.std_coef = 1.75
        self.least_trade_limit = 0.01
        self.commission = 0.15 / 100
        self.interval_sec = 30

    def update(self):
        # 30秒ごとに実行
        self.last_start = time.time()
        res, me = Trader.get_recent_data()
        sell_line, buy_line = self.set_trade_line(res)
        order = self.generate_order(me, sell_line, buy_line)
        if not order:
            pass
            # order_id = F.api_me('sendchildorder', 'POST', body=order)
            # logger.info('order id: %s, ', json.dumps(order_id))

    def run(self):
        while True:
            try:
                wait = max(0, self.interval_sec - (time.time() - self.last_start))
                time.sleep(wait)
                self.update()
            except Exception as e:
                logger.error(e)
                break

    @classmethod
    def get_recent_data(cls):
        # 最新100件の取引履歴
        res = pd.DataFrame(F.api('history'))
        # 資産状況
        me = F.api_me('getbalance')
        me = pd.DataFrame(me).set_index('currency_code')
        return res, me

    def set_trade_line(self, recent):
        # 過去のデータから，売買ラインを見極める
        mean = recent.price.mean()
        std = recent.price.std()
        sell_line = mean + std * self.std_coef
        buy_line = mean - std * self.std_coef
        return sell_line, buy_line

    def generate_order(self, me, sell_line, buy_line):
        # 注文を生成する
        ticker = F.api('ticker')
        mid_val = (ticker['best_bid'] + ticker['best_ask']) // 2
        jpy = me.loc['JPY'].available
        btc = me.loc['BTC'].available
        jpy_btc_val = jpy / mid_val

        order = {
            'product_code': 'BTC_JPY',
            'child_order_type': 'LIMIT',
            'price': int(mid_val),
            'minute_to_expire': 1,
        }

        if jpy_btc_val > self.least_trade_limit and mid_val < buy_line:
            order['size'] = jpy / (mid_val * (1 + self.commission))
            order['side'] = 'BUY'
        elif btc > self.least_trade_limit and mid_val > sell_line:
            order['size'] = btc * (mid_val * (1 - self.commission))
            order['side'] = 'SELL'
        else:
            return None
        logger.info('ORDER: %s    [price: %d]', json.dumps(order), mid_val)
        logger.debug('me: jpy=%s btc=%s', str(jpy), str(btc))
        return order
