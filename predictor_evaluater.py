from database.TradeHistory import get_session
from database.db_utils import get_recent_hist15_df
import datetime
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from chainer import serializers
from agent.model_def import MyChain


def zs(p, n, shift=0):
    return (p.shift(shift) - p.rolling(n).mean()) / p.rolling(n).std()


def avg(p, n):
    return p.rolling(n).mean()


def std(p, n):
    return p.rolling(n).std()


save_base_dir = 'agent/tmp/'
model_base_dir = 'agent/'
prefix = 'w1_'
week = 2
snapshot_size = 72
offset = 0
com = 0#0.15 / 100
ylim = (38000, 49000)


session = get_session()
past_time = datetime.datetime.utcnow() - datetime.timedelta(weeks=week)
df = get_recent_hist15_df(past_time, session)
df.exec_date = pd.to_datetime(df.exec_date)
df = df.set_index('exec_date')

bench_price = df.price
bench_size = df['size']
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

r_label_list = [
    'r', 'r_1', 'r_2',
]
for r_label in r_label_list:
    dfb[r_label] = 0
dfb['state'] = 0

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

dfz = dfb

indicator = dfz.reset_index().loc[:, 'pma12':'utctime']
price_history = dfz.reset_index().price

indicator['vma12'] = indicator.vma12.fillna(0)
indicator['vZ12'] = indicator.vZ12.fillna(0)

answer = price_history.shift(-1) / price_history - 1
answer = (answer > 0.0005) * 1 - (answer < -0.0005) * 1 + 1

indexer = indicator.dv96_672.notnull()

d_exp = indicator.loc[indexer]
d_obj = answer[indexer]
data = np.array(d_exp, dtype=np.float32)
t_data = np.array(d_obj, dtype=np.int32)

row, col = d_exp.shape

price_test = price_history[indexer]


amount = []
accs = []
wrong1 = []
wrong2 = []
res_list = []
for i in range(offset, snapshot_size):
    model = MyChain(col)
    serializers.load_npz(model_base_dir + 'snapshot_%02d.npz' % i, model)
    res = model(data).data

    result = d_obj.reset_index()
    result['predict'] = res.argmax(axis=1)

    jpy = 40000
    btc = 0
    x = []
    y_p = []
    y_jpy = []
    sz_all = price_test.size
    begin = 0
    prc = 0
    for j, (prc, pred) in enumerate(zip(price_test[begin:], result.predict[begin:])):
        if pred == 2 and jpy > 0:
            btc += jpy / (prc * (1 + com))
            jpy = 0
        elif pred == 0 and btc > 0:
            jpy += btc * (prc * (1 - com))
            btc = 0
        x.append(j)
        y_p.append(prc)
        y_jpy.append(jpy + btc * prc)

    amount.append(jpy + btc * prc)
    accs.append(result[result.price == result.predict].shape[0])
    wrong1.append(result[(result.price - result.predict).abs() == 1].shape[0])
    wrong2.append(result[(result.price - result.predict).abs() == 2].shape[0])

    res_list.append(result.groupby(['price', 'predict']).size())

    fig = plt.figure(figsize=(8, 10))
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)
    ax1.plot(x, y_jpy)
    ax1.set_ylim(*ylim)
    ax2.plot(x, y_p)
    fig.savefig(save_base_dir + prefix + 'fig_%02d.png' % i)
    plt.clf()


amt_df = pd.DataFrame({
    'amount': amount,
    'acc_num': accs,
    'acc_w1': wrong1,
    'acc_w2': wrong2,
})
amt_df.to_csv(save_base_dir + prefix + 'amount_acc.csv', sep='\t')
pd.concat(res_list, axis=1).fillna(0).to_csv(save_base_dir + prefix + 'detail.csv', sep='\t')
