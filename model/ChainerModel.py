import numpy as np
import pandas as pd
from chainer import Link, Chain, ChainList, cuda
import chainer.functions as F
import chainer.links as L

from database.db_utils import zs, avg, std

ls_1 = 400
ls_2 = 800
ls_4 = 800
ls_5 = 200
out_size = 3


class MyChain(Chain):
    def __init__(self, col):
        super().__init__(
            l1=L.Linear(col, ls_1),
            l2=L.Linear(ls_1, ls_2),
            l4=L.Linear(ls_2, ls_4),
            l5=L.Linear(ls_4, ls_5),
            l6=L.Linear(ls_5, out_size)
        )

    def __call__(self, x):
        h = F.sigmoid(self.l1(x))
        h = F.sigmoid(self.l2(h))
        h = F.leaky_relu(self.l4(h))
        h = F.sigmoid(self.l5(h))
        o = self.l6(h)
        return o


def history2indicator(df_15, r=0, r_1=0, r_2=0, state=0):
    # History15minデータを方針決定用のデータに変換
    bench_price = df_15.price
    bench_size = df_15['size']
    dfb = pd.DataFrame([bench_price, bench_size]).T

    p = dfb.price
    v = dfb['size']

    dfb['pma12'] = zs(p / avg(p, 12) - 1, 96)
    dfb['pma96'] = zs(p / avg(p, 96) - 1, 96)
    dfb['pma672'] = zs(p / avg(p, 672) - 1, 96)

    dfb['ma4_36'] = zs(avg(p, 4) / avg(p, 36) - 1, 96)
    dfb['ma12_96'] = zs(avg(p, 12) / avg(p, 96) - 1, 96)
    dfb['ac12_12'] = zs((p / avg(p, 12)) / avg(p / avg(p, 12), 12), 96)
    dfb['ac96_96'] = zs((p / avg(p, 96)) / avg(p / avg(p, 96), 12), 96)

    dfb['vma12'] = zs(v / avg(v, 12) - 1, 96)
    dfb['vma96'] = zs(v / avg(v, 96) - 1, 96)
    dfb['vma672'] = zs(v / avg(v, 672) - 1, 96)

    dfb['vZ12'] = zs(v, 12)
    dfb['vZ96'] = zs(v, 96)
    dfb['vZ672'] = zs(v, 672)

    # rや前の行動を保持しないといけない問題
    dfb['r'] = r
    dfb['r_1'] = r_1
    dfb['r_2'] = r_2
    dfb['state'] = state

    dfb['pZ12'] = zs(p, 12)
    dfb['pZ96'] = zs(p, 96)
    dfb['vol12'] = zs(std(p, 12), 96)
    dfb['vol96'] = zs(std(p, 96), 96)
    dfb['vol672'] = zs(std(p, 672), 96)
    dfb['dv12_96'] = zs(std(p, 12) / avg(std(p, 12), 96), 96)
    dfb['dv96_672'] = zs(std(p, 96) / avg(std(p, 96), 672), 96)

    for i in range(96):
        dfb['pZ96_s%02d' % i] = zs(p, 96, shift=i)

    dfb['pre_diff'] = p / p.shift(1) - 1

    dfb['max_diff12'] = p / p.rolling(12).max() - 1
    dfb['max_diff96'] = p / p.rolling(96).max() - 1
    dfb['max_diff672'] = p / p.rolling(672).max() - 1

    dfb['min_diff12'] = p / p.rolling(12).min() - 1
    dfb['min_diff96'] = p / p.rolling(96).min() - 1
    dfb['min_diff672'] = p / p.rolling(672).min() - 1

    dfb['utctime'] = (dfb.index.hour * 4 + dfb.index.minute / 15) / 96

    price = dfb.price.loc[dfb.index[-1]]
    price_pre = dfb.price.loc[dfb.index[-2]]
    # return last row
    return np.array(dfb.loc[dfb.index[-1], 'pma12':'utctime'], dtype=np.float32), price, price_pre