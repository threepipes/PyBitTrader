from Interface import CsvInterface
import Functions as F
from datetime import timedelta


def test_csvi(delta_sec=36000):
    start_date = F.str2date('2017-08-20T00:43:48.66') - timedelta(seconds=delta_sec)
    tool = CsvInterface('data/hist.csv', 60 * 60 * 24, start_date)
    for i in range(10000):
        ticker = tool.ticker()
        avg = tool.get_recent_avg()
        if ticker is None:
            break
        if ticker['best_bid_size'] == 0:
            # print('no ticker')
            ticker['best_bid'] = 'no ticker'
        if (i + 1) % 60 == 0:
            print(ticker['best_bid'], avg, ticker['timestamp'])


if __name__ == '__main__':
    test_csvi(60 * 60 * 24 * 10)
