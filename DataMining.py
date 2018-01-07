import time
from sqlalchemy.sql.expression import func

import Functions as F
from database.TradeHistory import History, get_session


class BoardMiner:
    def __init__(self):
        super().__init__()
        self.session = get_session()
        self.pre_hist_id, = self.session.query(
            func.min(History.id)
        ).first()
        self.last_req = 0
        self.sleep_time = 2

    def _add_history(self):
        payloads = {
            # 'after': self.pre_hist_id,
            'before': self.pre_hist_id,
            'count': 500,
        }
        hist = F.api('history', payloads=payloads)
        self.last_req = time.time()
        for h in hist:
            h['exec_date'] = F.str2date(h['exec_date'])
            hist_data = History(**h)
            self.session.add(hist_data)
            self.pre_hist_id = min(self.pre_hist_id, h['id'])
        if len(hist) == 0:
            # self.pre_hist_id += 500
            return False
        self.session.commit()
        return True

    def run(self):
        for i in range(30000):
            print(i, self.pre_hist_id)
            if not self._add_history():
                break
            slp = max(0, self.sleep_time - (time.time() - self.last_req))
            time.sleep(slp)


if __name__ == '__main__':
    miner = BoardMiner()
    miner.run()
