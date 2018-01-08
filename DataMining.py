import time
from sqlalchemy.sql.expression import func
from sqlalchemy import desc
import datetime

import Functions as F
from database.TradeHistory import History, get_session


class BoardMiner:
    def __init__(self):
        super().__init__()
        self.session = get_session()
        self.pre_hist_id, = self.session.query(
            func.max(History.id)
        ).first()
        self.last_req = 0
        self.sleep_time = 2

    def _add_history(self):
        payloads = {
            'after': self.pre_hist_id,
            'before': self.pre_hist_id + 500,
            'count': 500,
        }
        hist = F.api('history', payloads=payloads)
        self.last_req = time.time()
        for h in hist:
            h['exec_date'] = F.str2date(h['exec_date'])
            hist_data = History(**h)
            self.session.add(hist_data)
            self.pre_hist_id = max(self.pre_hist_id, h['id'])
        if len(hist) == 0:
            last = self.session.query(History).order_by(desc(History.id)).first()
            if datetime.datetime.utcnow() < last.exec_date + datetime.timedelta(minutes=1):
                return False
            self.pre_hist_id += 500 - 1
        self.session.commit()
        return True

    def run(self):
        for i in range(30000):
            print(i, self.pre_hist_id)
            if not self._add_history():
                self.sleep_time = 10
            slp = max(0, self.sleep_time - (time.time() - self.last_req))
            time.sleep(slp)


if __name__ == '__main__':
    miner = BoardMiner()
    miner.run()
