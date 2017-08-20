from SystemTrader import BoardData
import Functions as F
import time
from Database import Database


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


class ExecutionHistoryDB(Database):
    table_name = 'ExecutionHistory'
    key = 'id'
    column = F.execution_keys
    data_table = {
        'id': 'INT(10)',
        'side': 'VARCHAR(5)',
        'size': 'DOUBLE',
        'price': 'DOUBLE',
        'exec_date': 'DATETIME',
    }

    def __init__(self):
        super().__init__(
            self.table_name,
            self.key,
            self.column,
            self.data_table
        )


def create_hist_db():
    hdb = ExecutionHistoryDB()
    hdb.init_table()
    with open(data_path + 'hist.csv') as f:
        for i, row in enumerate(f):
            data = {}
            for key, col in zip(
                    ExecutionHistoryDB.column,
                    row.strip().split(',')):
                data[key] = col
            hdb.insert(data)
            if (i + 1) % 100 == 0:
                print(i + 1)
                hdb.commit()
    hdb.close()


if __name__ == '__main__':
    create_hist_db()
