# coding: UTF-8
import numpy as np
from gym import spaces
import random


class State:
    COM = 0 # 0.15 / 100

    def __init__(self, pre_price):
        self.did_buy = -1
        self.pre_trade_price = pre_price

    def _buy(self, price):
        reward = 1 - price / self.pre_trade_price - self.COM
        self.did_buy = 1
        self.pre_trade_price = price
        return reward

    def _sell(self, price):
        reward = 1 - self.pre_trade_price / price - self.COM
        self.did_buy = -1
        self.pre_trade_price = price
        return reward

    def trade(self, price):
        if self.did_buy == 1:
            return self._sell(price)
        else:
            return self._buy(price)


class History:
    TIME_UNIT = 24 * 5 * 4
    ACTIONS = 2  # 取れる行動の種類数
    OBS_SIZE = TIME_UNIT + 1  # エージェントの観察値の種類数 ここでは履歴長(300) + 前回価格(1)

    def __init__(self, price_hist):
        self.turn = 0
        self.price = price_hist  # btc価値推移(pd.Series:分刻み?) 0-indexed
        self.index = self.TIME_UNIT - 1
        self.mean = price_hist.rolling(self.TIME_UNIT).mean()
        self.action_space = spaces.Discrete(self.ACTIONS)

    def reset(self):
        """
        環境の初期化をする
        """
        self.index = random.randint(self.TIME_UNIT - 1, self.price.size - 1000)
        self.state = State(self.price[self.index])
        return self._get_observe()

    def _get_observe(self):
        if self.index == self.price.size:
            return None
        prices = self.price[self.index - (self.TIME_UNIT - 1): self.index + 1] / self.mean[self.index] - 1
        p = self.state.pre_trade_price / self.mean[self.index] - 1
        prices = prices.append(pd.Series(p))
        obs = np.array(prices * self.state.did_buy * -1, dtype=np.float32)
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
        price = self.price[self.index]
        reward = 0 #(1 - price / self.price[self.index - 1]) * self.state.did_buy + State.COM
        self.index += 1
        observe = self._get_observe()
#         print(observe)
        done = observe is None
        if action == 1:
            reward += self.state.trade(price) * 1.2
        info = 'price=%d idx=%d act=%d rwd=%f' % (
            price, self.index, action, reward
        )
        return observe, reward, done, info

    def get_action_space(self):
        """
        :return: Descrete: とれる行動の種類数を返す
        """
        return self.action_space.sample
