from utils.settings import get_logger

logger = get_logger().getChild(__file__)


class VirtualApi:
    def __init__(self):
        self.jpy = 40000
        self.btc = 0
        self.commission = 0.15 / 100

    def api_me(self, api_method, http_method='GET', body=None):
        if api_method == 'getbalance':
            return self._get_balance()
        if api_method == 'sendchildorder':
            return self._order(body)
        return None

    def _get_balance(self):
        data = [
            {
                'currency_code': 'JPY',
                'available': self.jpy,
            },
            {
                'currency_code': 'BTC',
                'available': self.btc,
            }
        ]
        return data

    def _order(self, order):
        price = order['price']
        size = order['size']
        side = order['side']
        before = self.jpy + price * self.btc
        if side == 'BUY':
            self.btc += size
            self.jpy -= size * (1 + self.commission) * price
        else:
            self.btc -= size * (1 + self.commission)
            self.jpy += size * price
        self.jpy = int(self.jpy)
        after = self.jpy + price * self.btc
        logger.debug('virtual: %f -> %f', before, after)
        return '-'