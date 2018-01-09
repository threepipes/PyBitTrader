import sqlite3
import pandas as pd
import chainer
import chainerrl
from gym import spaces
from model.TradeModel2 import TradeEnv as History


def zs(p, n):
    return (p - p.rolling(n).mean()) / p.rolling(n).std()


def avg(p, n):
    return p.rolling(n).mean()


def std(p, n):
    return p.rolling(n).std()


def make_agent(obs_size, n_actions):
    """
    チュートリアル通りのagent作成
    ネットワークやアルゴリズムの決定
    """
    n_hidden_channels = History.OBS_SIZE * 10
    n_hidden_layers = 10
    # 幅n_hidden_channels，隠れ層n_hidden_layersのネットワーク
    q_func = chainerrl.q_functions.FCStateQFunctionWithDiscreteAction(
        obs_size, n_actions, n_hidden_channels, n_hidden_layers
    ).to_gpu(1)

    # 最適化関数の設定
    optimizer = chainer.optimizers.Adam(1e-2)
    optimizer.setup(q_func)

    # 割引率の設定
    gamma = 0.9

    # 探索方針の設定
    explorer = chainerrl.explorers.ConstantEpsilonGreedy(
        epsilon=0.3, random_action_func=spaces.Discrete(n_actions).sample
    )

    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(10 ** 6)

    agent = chainerrl.agents.DoubleDQN(
        q_func, optimizer, replay_buffer, gamma, explorer,
        replay_start_size=500, gpu=1
    )
    return agent


def train_module(env, agent):
    """
    chainerrlのモジュールによるtraining
    """
    import logging
    import gym
    gym.undo_logger_setup()  # Turn off gym's default logger settings
#     logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='')

    handler = logging.FileHandler(filename="dqn8.log")
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger = logging.getLogger('chainerrl_logger_8')
    # logger.propagate = False
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    episode_len = 100
    chainerrl.experiments.train_agent_with_evaluation(
        agent, env,
        steps=episode_len*100000,           # 合計10000ステップagentを動かす
        eval_n_runs=10,         # 本番テストのたびに 5回評価を行う
        max_episode_len=episode_len,   # 1ゲームのステップ数
        eval_interval=episode_len*20,   # 1000ステップごとに本番テストを行う
        logger=logger,
        outdir='agent/result_8') # Save everything to 'agent/result' directory


db_name = 'db.sqlite3'
con = sqlite3.connect(db_name)
print('loading from db')
df = pd.read_sql_query('select * from history limit 500000 offset 4000000', con)
print('loaded from db')
df.exec_date = pd.to_datetime(df.exec_date)
df = df.set_index('exec_date')
df = df.loc['2016-03':]
df = df[['id', 'side', 'price', 'size']]
bench_price = df.price.resample('15Min').mean().fillna(method='ffill')
bench_size = df['size'].resample('15Min').sum().fillna(0)
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
dfb['utctime'] = (dfb.index.hour * 4 + dfb.index.minute / 15) / 96

dfz = dfb

indicator = dfz.reset_index().loc[:, 'pma12':'utctime']
price_history = dfz.reset_index().price

indicator['vma12'] = indicator.vma12.fillna(0)
indicator['vZ12'] = indicator.vZ12.fillna(0)

print('creating env')
env = History(price_history, indicator)

print('make agent')
obs_size = env.OBS_SIZE
n_actions = env.ACTIONS
agent = make_agent(obs_size, n_actions)

save_path = 'agent/trade8'
# agent.load(save_path)

# training
print('traning started')
train_module(env, agent)
agent.save(save_path)
print('traning finished')
