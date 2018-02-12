# coding: UTF-8
import numpy as np
import pandas as pd
from chainer import Link, Chain, ChainList, cuda
import chainer.functions as F
import chainer.links as L

from database.db_utils import zs, avg, std

input_size = 1238
ls_1 = 1000
ls_2 = 2000
ls_3 = 2000
ls_4 = 600
out_size = 3


class MyChain(Chain):
    def __init__(self):
        super().__init__(
            l1=L.Linear(input_size, ls_1),
            l2=L.Linear(ls_1, ls_2),
            l3=L.Linear(ls_2, ls_3),
            l4=L.Linear(ls_3, ls_4),
            l5=L.Linear(ls_4, out_size)
        )

    def __call__(self, x):
        h = F.sigmoid(self.l1(x))
        h = F.sigmoid(self.l2(h))
        h = F.leaky_relu(self.l3(h))
        h = F.sigmoid(self.l4(h))
        o = self.l5(h)
        return o


def history2indicator(df_15, r=0, r_1=0, r_2=0, state=0):
    # History15minデータを方針決定用のデータに変換
    bench_price = df_15.price
    bench_size = df_15['size']
    dfb = pd.DataFrame([bench_price, bench_size]).T

    p = dfb.price
    v = dfb['size']

    base = 96

    dfb['pma12'] = zs(p / avg(p, 12) - 1, base)
    dfb['pma96'] = zs(p / avg(p, 96) - 1, base)
    dfb['pma672'] = zs(p / avg(p, 672) - 1, base)
    dfb['pma1440'] = zs(p / avg(p, 1440) - 1, base)

    dfb['ma4_36'] = zs(avg(p, 4) / avg(p, 36) - 1, base)
    dfb['ma12_96'] = zs(avg(p, 12) / avg(p, 96) - 1, base)
    dfb['ma60_600'] = zs(avg(p, 60) / avg(p, 600) - 1, base)
    dfb['ac12_12'] = zs((p / avg(p, 12)) / avg(p / avg(p, 12), 12), base)
    dfb['ac96_96'] = zs((p / avg(p, 96)) / avg(p / avg(p, 96), 12), base)
    dfb['ac600_600'] = zs((p / avg(p, 600)) / avg(p / avg(p, 600), 12), base)

    dfb['vma12'] = zs(v / avg(v, 12) - 1, base)
    dfb['vma96'] = zs(v / avg(v, 96) - 1, base)
    dfb['vma672'] = zs(v / avg(v, 672) - 1, base)
    dfb['vma1440'] = zs(v / avg(v, 1440) - 1, base)

    dfb['vZ12'] = zs(v, 12)
    dfb['vZ96'] = zs(v, 96)
    dfb['vZ672'] = zs(v, 672)
    dfb['vZ1440'] = zs(v, 1440)

    dfb['pZ12'] = zs(p, 12)
    dfb['pZ96'] = zs(p, 96)
    dfb['pZ600'] = zs(p, 600)
    dfb['pZ1440'] = zs(p, 1440)
    dfb['vol12'] = zs(std(p, 12), base)
    dfb['vol96'] = zs(std(p, 96), base)
    dfb['vol672'] = zs(std(p, 672), base)
    dfb['vol1440'] = zs(std(p, 1440), base)
    dfb['dv12_96'] = zs(std(p, 12) / avg(std(p, 12), 96), base)
    dfb['dv96_672'] = zs(std(p, 96) / avg(std(p, 96), 672), base)
    dfb['dv600_1440'] = zs(std(p, 600) / avg(std(p, 600), 1440), base)

    for i in range(600):
        dfb['pZ96_s%02d' % i] = zs(p, 96, shift=i)

    for i in range(600):
        dfb['pre_diff%02d' % i] = p.shift(i) / p.shift(i + 1) - 1

    dfb['max_diff12'] = p / p.rolling(12).max() - 1
    dfb['max_diff96'] = p / p.rolling(96).max() - 1
    dfb['max_diff672'] = p / p.rolling(672).max() - 1
    dfb['max_diff1440'] = p / p.rolling(1440).max() - 1

    dfb['min_diff12'] = p / p.rolling(12).min() - 1
    dfb['min_diff96'] = p / p.rolling(96).min() - 1
    dfb['min_diff672'] = p / p.rolling(672).min() - 1
    dfb['min_diff1440'] = p / p.rolling(1440).min() - 1

    dfb['utctime'] = (dfb.index.hour * 60 + dfb.index.minute) / 1440

    price = dfb.price.loc[dfb.index[-1]]
    price_pre = dfb.price.loc[dfb.index[-2]]
    # return last row
    return np.array(dfb.loc[dfb.index[-1], 'pma12':'utctime'], dtype=np.float32), price, price_pre
