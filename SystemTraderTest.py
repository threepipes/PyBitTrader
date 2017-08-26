import datetime
import random

from SystemTrader import RecentData
from Functions import date2str


def test_recentdata(rev=False):
    recent = RecentData(60) # 1m
    now_time = datetime.datetime.now().timestamp()
    prev_delta = 0
    if rev:
        sgn = -1
    else:
        sgn = 1
    for i in range(500):
        prev_delta += random.randint(1, 10) * sgn
        t = datetime.datetime.fromtimestamp(now_time + prev_delta)
        data = {
            'size': random.random(),
            'price': random.randint(1, 10),
            'exec_date': date2str(t),
        }
        print('add', data)
        recent.add(data, rev=rev)
        print(str(recent), len(recent.data_list), recent.queue_diff())


if __name__ == '__main__':
    test_recentdata()
