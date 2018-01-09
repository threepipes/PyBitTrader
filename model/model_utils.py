import chainer
import chainerrl
from gym import spaces

from model.TradeModel2 import TradeEnv


def make_agent(obs_size, n_actions):
    """
    チュートリアル通りのagent作成
    ネットワークやアルゴリズムの決定
    """
    n_hidden_channels = obs_size * 2
    n_hidden_layers = 2
    # 幅n_hidden_channels，隠れ層n_hidden_layersのネットワーク
    q_func = chainerrl.q_functions.FCStateQFunctionWithDiscreteAction(
        obs_size, n_actions, n_hidden_channels, n_hidden_layers
    )

    # 最適化関数の設定
    optimizer = chainer.optimizers.Adam(1e-2)
    optimizer.setup(q_func)

    # 割引率の設定
    gamma = 0.95

    # 探索方針の設定
    explorer = chainerrl.explorers.ConstantEpsilonGreedy(
        epsilon=0.3, random_action_func=spaces.Discrete(n_actions).sample
    )

    replay_buffer = chainerrl.replay_buffer.ReplayBuffer(10 ** 6)

    agent = chainerrl.agents.DoubleDQN(
        q_func, optimizer, replay_buffer, gamma, explorer,
        replay_start_size=500
    )
    return agent


def load_agent(model_path='agent/model'):
    agent = make_agent(TradeEnv.OBS_SIZE, TradeEnv.ACTIONS)
    agent.load(model_path)
    return agent
