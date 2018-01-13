from chainer import Link, Chain, ChainList, cuda
import chainer.functions as F
import chainer.links as L

ls_1 = 500
ls_2 = 1000
ls_3 = 1000
ls_4 = 200


class MyChain(Chain):
    def __init__(self, in_size, out_size=3):
        super().__init__(
            l1=L.Linear(in_size, ls_1),
            l2=L.Linear(ls_1, ls_2),
            l3=L.Linear(ls_2, ls_3),
            l4=L.Linear(ls_3, ls_4),
            l5=L.Linear(ls_4, out_size)
        )

    def __call__(self, x):
        h1 = F.sigmoid(self.l1(x))
        h2 = F.sigmoid(self.l2(h1))
        h3 = F.sigmoid(self.l3(h2))
        h4 = F.sigmoid(self.l4(h3))
        o = self.l5(h4)
        return o
