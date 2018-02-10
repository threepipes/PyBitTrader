from flask import Flask, render_template, request
import pandas as pd
from plot.Plot import plot_recent_order
from database.TradeHistory import get_engine
from logging import getLogger

logger = getLogger(__file__)
app = Flask(__name__)


@app.route('/')
def hello():
    return 'hello bitcoin trader'


@app.route('/order')
def result_all():
    size = request.args.get('size', 200)
    if not isinstance(size, int):
        logger.warning('wrong arg type: size must be int but %s', type(size))
        size = 200
    content = plot_order(size)
    return render_template('result.html', title='order', item_list=content)


def plot_order(size):
    base = "select * from orderdata where child_order_id='coincheck-order'"
    o1 = pd.read_sql(base + " limit 1", get_engine())
    df = pd.read_sql(base + " order by id limit %d" % size, get_engine())
    html = plot_recent_order(o1, df)
    content = [{
        'plot': html,
        'name': 'order',
    }]
    return content


if __name__ == '__main__':
    app.run(host='0.0.0.0')
