from Interface import CsvInterface
from utils import BitFlyer as F
from datetime import timedelta

from matplotlib import pyplot as plt


def test_csvi(delta_sec=36000):
    start_date = F.str2date('2017-08-20T00:43:48.66') - timedelta(seconds=delta_sec)
    tool = CsvInterface('data/hist.csv', 60 * 30, start_date)
    y_bid = []
    y_avg = []
    y_upper = []
    y_upper2 = []
    y_lower = []
    y_lower2 = []
    x = []
    for i in range(delta_sec):
        ticker = tool.ticker()
        avg = tool.get_recent_avg()
        sigma = tool.recent.sigma()
        if ticker is None:
            break
        if ticker['best_bid_size'] == 0:
            # print('no ticker')
            ticker['best_bid'] = 'no ticker'
        y_bid.append(ticker['best_bid'])
        y_avg.append(avg)
        y_upper.append(avg + sigma)
        y_upper2.append(avg + sigma * 2)
        y_lower.append(avg - sigma)
        y_lower2.append(avg - sigma * 2)
        x.append(i)
        if (i + 1) % 60 == 0:
            print(ticker['best_bid'], avg, tool.recent.sigma(), ticker['timestamp'])

    plt.plot(x, y_bid)
    plt.plot(x, y_avg)
    plt.plot(x, y_lower)
    plt.plot(x, y_lower2)
    plt.plot(x, y_upper)
    plt.plot(x, y_upper2)
    plt.show()


if __name__ == '__main__':
    test_csvi(60 * 60 * 25)
