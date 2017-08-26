from datetime import datetime as dt
from datetime import timedelta
from SystemTrader import RecentData
import Functions as F


class Interface:
    """
    外部取引, CSV, DB等共通のインターフェース
    """
    def __init__(self, span):
        self.span = span

    def init_recent(self, now: dt):
        span = self.span
        oldest = self.latest_id()
        limit = now - timedelta(seconds=span)
        self.latest = oldest
        self.recent = RecentData(span)
        while True:
            hist = self.get_hist(before=oldest, size=500)
            for row in hist:
                if F.str2date(row['exec_date']) < limit:
                    return
                oldest = row['id']
                self.recent.add(row, rev=True)

    def latest_id(self):
        """
        最新の約定idを取得する
        :return: 最新id
        """
        raise NotImplementedError()

    def ticker(self):
        raise NotImplementedError()

    def get_hist(self, before=None, after=None, size=100):
        """
        区間(after, before)の最新min(500, size)件の約定履歴を取得
        :param before: このidより前の約定履歴をとる
        :param after: このidより後の約定履歴をとる
        :param size: 取得する約定履歴数の最大値
        :return: 約定履歴のリスト(時間降順)
        """
        raise NotImplementedError()

    def get_recent_avg(self):
        """
        ここspan[sec]の取引成立金額の平均
        span: init_recentで指定した期間
        """
        return self.recent.average()

    def ticker(self):
        """
        ticker情報
        """
        raise NotImplementedError()


class CsvInterface(Interface):
    def __init__(self, file_name, span, start_date=dt.now()):
        super().__init__(span)
        self.file_name = file_name
        self.database = []
        self.start_date = start_date
        self.now = dt.fromtimestamp(start_date.timestamp())
        self._load_csv()
        # self._set_row_id()
        self.init_recent(self.now)

    def _set_row_id(self):
        latest = len(self.database) - 1
        oldest = 0
        ans = oldest
        while latest >= oldest:
            mid = (latest + oldest) // 2
            if self._is_past(mid):
                ans = mid
                oldest = mid + 1
            else:
                latest = mid - 1
        self.current_latest = ans

    def _is_past(self, _id):
        return self.database[_id]['date'] < self.now

    def _load_csv(self):
        """
        format: [id,side,price,size,exec_date]
        dateの最新は2017-08-20T00:43:48.66
        dateの最古は2017-06-27T18:36:14.07
        :return:
        """
        limit = self.start_date - timedelta(seconds=self.span + 100)
        with open(self.file_name) as f:
            for row in f:
                row_data = row.strip().split(',')
                _id, _, _pr, _sz, _dt = row_data
                if '.' not in _dt:
                    _dt += '.0'
                data = {
                    'price': float(_pr),
                    'size': float(_sz),
                    'exec_date': _dt,
                    'date': F.str2date(_dt)
                }
                if data['date'] < limit:
                    break
                self.database.append(data)
        self.database = list(reversed(self.database))
        for i, data in enumerate(self.database):
            data['id'] = i
            if data['date'] <= self.start_date:
                self.current_latest = i

    def ticker(self):
        """
        CSVの場合bidもaskもないので，
        bid=ask=最新約定価格
        1秒進めて最新の約定履歴を得る
        """
        self.now += timedelta(seconds=1)
        db = self.database
        latest = None
        dbsize = len(db)
        while self.current_latest < dbsize - 1 and db[self.current_latest + 1]['date'] <= self.now:
            self.current_latest += 1
            latest = db[self.current_latest]
            self.recent.add(latest)
        if self.current_latest >= dbsize - 1:
            return None
        if latest is None:
            latest = db[self.current_latest]
        return {
            'best_bid': latest['price'],
            'best_ask': latest['price'],
            'best_bid_size': latest['size'],
            'best_ask_size': latest['size'],
            'timestamp': F.date2str(self.now),
            'ltp': latest['price']
        }

    def latest_id(self):
        return self.database[self.current_latest]['id']

    def get_hist(self, before=None, after=None, size=100):
        if before is None or before > self.current_latest:
            before = self.current_latest
        if after is None or after < 0:
            after = 0
        if before - after < 2 or size <= 0:
            return []
        size = min(size, 500, before - after - 1)
        return list(reversed(self.database[before - size: before]))
