import matplotlib
matplotlib.use('Agg')

import pandas as pd
import mpld3
from matplotlib import pyplot as plt


def plot_recent_order(cc_order):
    resource = cc_order.price * cc_order['size']
    sr_res = resource / resource[0]
    sr_gen = cc_order.price / cc_order.price[0]
    plot_df = pd.DataFrame([sr_res, sr_gen], index=['resource', 'price']).T
    fig = plot_df.plot(figsize=(15, 5)).get_figure()
    html = mpld3.fig_to_html(fig)
    plt.clf()
    return html
