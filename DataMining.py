import time
from sqlalchemy.sql.expression import func
from sqlalchemy import desc
import datetime
from requests.exceptions import ConnectionError
import pandas as pd

from utils import BitFlyer as F
from database.TradeHistory import History, History15min, get_session
from database.db_utils import get_recent_hist_df
from utils.settings import logging_config, get_logger

logger = get_logger().getChild(__file__)


class BoardMiner:
    def __init__(self):
        super().__init__()
        self.session = get_session()
        self.pre_hist_id, = self.session.query(
            func.max(History.id)
        ).first()
        self.last_req = 0
        self.sleep_time = 1

    def _add_history(self):
        payloads = {
            'after': self.pre_hist_id,
            'before': self.pre_hist_id + 500,
            'count': 500,
        }
        hist = F.api('history', payloads=payloads)
        if hist is None:
            time.sleep(60)
            return True
        self.last_req = time.time()
        for h in hist:
            h['exec_date'] = F.str2date(h['exec_date'])
            hist_data = History(**h)
            self.session.add(hist_data)
            self.pre_hist_id = max(self.pre_hist_id, h['id'])
        if len(hist) == 0:
            if not self._check_latest():
                return False
            self.pre_hist_id += 500 - 1
        self.session.commit()
        self._set_hist15()
        return True

    def _check_latest(self):
        # Falseならpre_hist_idを500進める
        time.sleep(1)
        hist = F.api('history', payloads={'count': 1})
        latest_id = hist[0]['id']
        db_latest = self.session.query(History).order_by(
            desc(History.exec_date)
        ).first().id
        return db_latest + 500 <= latest_id

    def _set_hist15(self):
        latest_15data_time = self.session.query(History15min).order_by(
            desc(History15min.exec_date)
        ).first().exec_date
        latest_histdata_time = self.session.query(History).order_by(
            desc(History.exec_date)
        ).first().exec_date
        if latest_15data_time >= latest_histdata_time - datetime.timedelta(minutes=30):
            return
        logger.debug('set hist15')
        df = get_recent_hist_df(latest_15data_time + datetime.timedelta(minutes=15), self.session)
        df.exec_date = pd.to_datetime(df.exec_date)
        df = df.set_index('exec_date')
        bench_price = df.price.resample('15Min').mean().fillna(method='ffill')
        bench_size = df['size'].resample('15Min').sum().fillna(0)
        dfb = pd.DataFrame([bench_price, bench_size]).T
        until = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)
        logger.debug(dfb.loc[:until])
        dfb.loc[:until].to_sql('history15min', self.session.bind, chunksize=1000, if_exists='append')

    def run(self):
        while True:
            try:
                logger.info(self.pre_hist_id)
                if not self._add_history():
                    # 最新の取引まで確保できていることを確認すべき
                    self.sleep_time = 10
                slp = max(0, self.sleep_time - (time.time() - self.last_req))
                time.sleep(slp)
            except ConnectionError as e:
                logger.error('Error: hist_id=%d', self.pre_hist_id)
                logger.error(e)
                self.sleep_time = 2
                time.sleep(60 * 5)


if __name__ == '__main__':
    logging_config()
    miner = BoardMiner()
    miner.run()
