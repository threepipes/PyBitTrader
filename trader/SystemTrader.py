import time
from collections import deque
from datetime import timedelta
from queue import Queue

import math
import numpy as np
from matplotlib import pyplot as plt

from utils import BitFlyer as F


def add_queue(qu: Queue, data):
    qu.put(data)
    if qu.full():
        qu.get()


class Status:
    def __init__(self):
        self.jpy = 20000
        self.btc = 0


class Trader:
    def __init__(self):
        pass



class RecentData:
    def __init__(self, span):
        """
        :param span: timesec
        """
        self.data_list = deque()
        self.amount = 0
        self.value = 0
        self.sqval = 0
        self.span = span
        self.last_date = 0

    def add(self, row: dict, rev=False):
        """
        :param row: dict{size, price, exec_date}
        :return: None
        """
        _size = row['size']
        _price = row['price']
        _time = row['exec_date']
        _date = F.str2date(_time)
        data = {
            'size': _size,
            'price': _price,
            'time': _date,
            'sqval': _price ** 2 * _size
        }
        self.amount += _size
        self.value += _price * _size
        self.sqval += data['sqval']
        if rev:
            self.data_list.appendleft(data)
            self.remove_top(_date)
        else:
            self.data_list.append(data)
            self.remove(_date)

    def remove(self, _date):
        limit = _date - timedelta(seconds=self.span)
        while self.data_list[0]['time'] < limit:
            pop = self.data_list.popleft()
            self.amount -= pop['size']
            self.value -= pop['price'] * pop['size']
            self.sqval -= pop['sqval']

    def remove_top(self, _date):
        limit = _date + timedelta(seconds=self.span)
        while self.data_list[-1]['time'] > limit:
            pop = self.data_list.pop()
            self.amount -= pop['size']
            self.value -= pop['price'] * pop['size']
            self.sqval -= pop['sqval']

    def average(self):
        if self.amount == 0:
            return 0
        return self.value / self.amount

    def sigma(self):
        return math.sqrt(self.sqval / self.amount - self.average() ** 2)

    def update(self):
        pass

    def queue_diff(self):
        return self.data_list[-1]['time'] - self.data_list[0]['time']

    def __str__(self):
        return '(amt:%f, val:%f, avg:%f)' % (
            self.amount, self.value, self.average()
        )


class BoardData:
    max_queue = 20000
    dump_path = 'data/board/'
    column = [
        'id', 'value'
    ]

    def __init__(self):
        self.pre_hist_id = 0
        self.buy_data = Queue(self.max_queue)
        self.sell_data = Queue(self.max_queue)

    def render(self):
        x_buy = list(self.buy_data)
        x_sel = list(self.sell_data)

    def get_board(self):
        board = F.api('board', {'count': 1})
        return board

    def dump(self):
        buy_list = []
        sel_list = []
        with open(self.dump_path + 'buy.csv', 'a') as f:
            while not self.buy_data.empty():
                data = self.buy_data.get()
                buy_list.append(data)
                f.write(F.dumps(data, self.column) + '\n')

        with open(self.dump_path + 'sell.csv', 'a') as f:
            while not self.sell_data.empty():
                data = self.sell_data.get()
                sel_list.append(data)
                f.write(F.dumps(data, self.column) + '\n')

        return buy_list, sel_list

    def load(self):
        with open(self.dump_path + 'buy.csv') as f:
            for row in f:
                _id, _val = row.strip().split(',')
                _id = int(_id)
                _val = float(_val)
                self.pre_hist_id = max(self.pre_hist_id, _id)
                add_queue(self.buy_data, {'id': _id, 'value': _val})

        with open(self.dump_path + 'sell.csv') as f:
            for row in f:
                _id, _val = row.strip().split(',')
                _id = int(_id)
                _val = float(_val)
                self.pre_hist_id = max(self.pre_hist_id, _id)
                add_queue(self.sell_data, {'id': _id, 'value': _val})

    def add_history(self):
        payloads = {
            'after': self.pre_hist_id,
            'count': 1000
        }
        hist = F.api('history', payloads=payloads)
        print(len(hist), self.pre_hist_id)
        for row in reversed(hist):
            _id = row['id']
            _type = row['side']
            _value = row['price']
            self.pre_hist_id = max(_id, self.pre_hist_id)
            data = {'id': _id, 'value': _value}
            if _type == 'SELL':
                add_queue(self.sell_data, data)
            else:
                add_queue(self.buy_data, data)


# def dump_board(board_info):
#     print('mid', board_info['mid_price'])
#     print('bids', board_info['bids'][0])
#     print('asks', board_info['bids'][0])

def run(board):
    trader = Trader()

    count = 0

    while True:
        board._add_history()
        # print(board.get_board())
        time.sleep(2)
        count += 1
        if count >= 3:
            break
    
    # board.dump()


def render(buy, sel):
    x_buy = []
    x_sel = []
    for b, s in zip(buy, sel):
        x_buy.append(b['value'])
        x_sel.append(s['value'])

    x = np.arange(len(x_buy))

    p1, = plt.plot(x, x_buy)
    p2, = plt.plot(x, x_sel)
    plt.legend([p1, p2], ['buy', 'sel'])
    plt.show()


if __name__ == '__main__':
    board = BoardData()
    # board.load()
    try:
        run(board)
    except KeyboardInterrupt:
        print('interrupted')
    buy, sel = board.dump()
    render(buy, sel)
