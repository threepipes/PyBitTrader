import time

import Functions as F
from trader.SystemTrader import BoardData

data_path = 'data/board/'


class BoardMiner(BoardData):
    def __init__(self):
        super().__init__()
        self.pre_hist_id = 100000000
        self.last_req = 0

    def add_history(self):
        payloads = {
            'before': self.pre_hist_id,
            'count': 500,
        }
        hist = F.api('history', payloads=payloads)
        self.last_req = time.time()
        # print(len(hist), self.pre_hist_id)
        with open(self.dump_path + 'hist.csv', 'a') as f:
            for row in hist:
                data = []
                _id = row['id']
                self.pre_hist_id = min(_id, self.pre_hist_id)
                for key in F.execution_keys:
                    data.append(str(row[key]))
                f.write(','.join(data) + '\n')

    def run(self):
        for i in range(3600):
            print(i)
            self.add_history()
            slp = max(0, 1 - (time.time() - self.last_req))
            time.sleep(slp)


if __name__ == '__main__':
    pass
