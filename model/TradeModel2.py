import numpy as np
from gym import spaces
import random


class History:
    OFFSET = 861
    ACTIONS = 5  # 取れる行動の種類数
    OBS_SIZE = 25  # エージェントの観察値の種類数 ここでは履歴長(300) + 前回価格(1)
    EPISODE_LEN = 200

    def __init__(self, price_hist, indicator):
        self.price = price_hist  # btc価値推移(pd.Series:分刻み?) 0-indexed
        self.indicator = indicator
        self.index = self.OFFSET
        self.action_space = spaces.Discrete(self.ACTIONS)

    def reset(self):
        """
        環境の初期化をする
        """
        self.index = random.randint(self.OFFSET - 1, self.price.size - self.EPISODE_LEN - 3)
        return self._get_observe()

    def _get_observe(self):
        if self.index == self.price.size - 3:
            return None
        obs = np.array(self.indicator.loc[self.index], dtype=np.float32)
#         print(self.price[self.index - self.TIME_UNIT - 1: self.index + 1])
        return obs

    def render(self):
        """
        ステップごとの描画関数
        """
        pass

    def step(self, action):
        """
        agentが選んだ行動が与えられるので
        環境を変更し，観察値や報酬を返す

        :param int action: どの行動を選んだか
        :return:
            observe: numpy array: 環境の観察値を返す
            reward : float      : 報酬
            done   : boolean    : 終了したか否か
            info   : str (自由?): (デバッグ用などの)情報
        """
        pre_obs = self.indicator.loc[self.index]
        action_pre = pre_obs['state']
        price_pre = self.price[self.index]
        self.index += 1
        price = self.price[self.index]
        reward = action_pre * (price / price_pre - 1)
        if action != action_pre:
            reward -= abs(action - action_pre) * 0.15 / 100
        self.indicator.loc[self.index, 'r'] = reward
        self.indicator.loc[self.index + 1, 'r_1'] = reward
        self.indicator.loc[self.index + 2, 'r_2'] = reward
        self.indicator.loc[self.index, 'state'] = action

        observe = self._get_observe()
        done = observe is None
        info = 'price=%d idx=%d act=%d rwd=%f' % (
            price, self.index, action, reward
        )
        return observe, reward, done, info

    def get_action_space(self):
        """
        :return: Descrete: とれる行動の種類数を返す
        """
        return self.action_space.sample
