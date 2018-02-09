import sys
import pandas as pd
import time
import chainer
from chainer import training
from chainer import datasets, iterators, optimizers, serializers
from chainer import Chain, cuda
import chainer.functions as F
import chainer.links as L
from chainer.training import extensions
from database.TradeHistory import get_session


name = sys.argv[1]
l_n = []
for a in sys.argv[2:]:
    l_n.append(int(a))

print(l_n)

if len(l_n) != 4:
    sys.exit(0)


def zs(p, n, shift=0):
    return (p.shift(shift) - p.rolling(n).mean()) / p.rolling(n).std().replace(0, 1)


def avg(p, n):
    return p.rolling(n).mean()


def std(p, n):
    return p.rolling(n).std()


session = get_session()

start = time.time()
print('loading from db')
df = pd.read_sql_query('select * from history1min', session.bind)
print('loaded from db: %fs' % (time.time() - start))
df.exec_date = pd.to_datetime(df.exec_date)
df = df.set_index('exec_date')
df = df.loc['2017':]

dfb = df

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

dfz = dfb

indicator = dfz.reset_index().loc[:, 'pma12':'utctime']
price_history = dfz.reset_index().price

indicator['vma12'] = indicator.vma12.fillna(0)
indicator['vZ12'] = indicator.vZ12.fillna(0)

answer = price_history.shift(-2) / price_history - 1
answer = pd.qcut(answer, 3, labels=list(range(3))).fillna(1)

indexer = indicator.dv96_672.notnull()
for label in indicator.columns:
    indexer = indexer & indicator[label].notnull()

xp = cuda.cupy

d_exp = indicator.loc[indexer].reset_index(drop=True)
d_obj = answer[indexer].reset_index(drop=True)

border = d_exp.index[-1800 * 5]
# last = d_exp.index[-200]
test_exp = d_exp[border:]
test_obj = d_obj[border:]
d_exp = d_exp[:border]
d_obj = d_obj[:border]

data = xp.array(d_exp, dtype=xp.float32)
t_data = xp.array(d_obj, dtype=xp.int32)
data_test = xp.array(test_exp, dtype=xp.float32)
t_data_test = xp.array(test_obj, dtype=xp.int32)

row, col = d_exp.shape

ls_1 = l_n[0]
ls_2 = l_n[1]
ls_3 = l_n[2]
ls_4 = l_n[3]
# ls_5 = 200
out_size = 3


class MyChain(Chain):
    def __init__(self):
        super().__init__(
            l1=L.Linear(col, ls_1),
            l2=L.Linear(ls_1, ls_2),
            l3=L.Linear(ls_2, ls_3),
            l4=L.Linear(ls_3, ls_4),
            #             l5=L.Linear(ls_4, ls_5),
            l5=L.Linear(ls_4, out_size)
        )

    def __call__(self, x):
        if chainer.config.train:
            h = F.dropout(F.sigmoid(self.l1(x)), ratio=0.5)
            #             h = F.dropout(F.sigmoid(self.l2(h)), ratio=0.01)
            h = F.dropout(F.sigmoid(self.l2(h)), ratio=0.5)
            h = F.dropout(F.leaky_relu(self.l3(h)), ratio=0.5)
            h = F.dropout(F.sigmoid(self.l4(h)), ratio=0.5)
        else:
            h = F.sigmoid(self.l1(x))
            #             h = F.sigmoid(self.l2(h))
            h = F.sigmoid(self.l2(h))
            h = F.leaky_relu(self.l3(h))
            h = F.sigmoid(self.l4(h))
        o = self.l5(h)
        return o


batch_size = 400

train = datasets.tuple_dataset.TupleDataset(data, t_data)
train = iterators.SerialIterator(train, batch_size=batch_size, shuffle=True, repeat=True)

testset = datasets.tuple_dataset.TupleDataset(data_test, t_data_test)
testset = iterators.SerialIterator(testset, batch_size=batch_size, shuffle=False, repeat=False)


model = L.Classifier(MyChain())
# serializers.load_npz('agent/%s.npz' % name, model.predictor)

gpu_device = 0
cuda.get_device_from_id(gpu_device).use()
model.to_gpu(gpu_device)

optimizer = optimizers.SGD()
optimizer.setup(model)
updater = training.StandardUpdater(train, optimizer, device=gpu_device)
# interval = 25
# times = 80
# for i in range(times):
trainer = training.Trainer(updater, (5000, 'epoch'), out='result/' + name)
trainer.extend(extensions.Evaluator(testset, model, device=gpu_device))
trainer.extend(extensions.LogReport())
trainer.extend(extensions.snapshot_object(model.predictor, 'optimizer_snapshot_{.updater.epoch}'))
trainer.extend(extensions.PrintReport([
    'epoch', 'main/loss', 'validation/main/loss',
    'main/accuracy', 'validation/main/accuracy', 'elapsed_time'
]))
trainer.extend(extensions.ProgressBar(update_interval=10))
trainer.run()
model.to_cpu()
serializers.save_npz('agent/%s.npz' % name, model.predictor)
model.to_gpu(gpu_device)
