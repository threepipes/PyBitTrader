from flask import Flask, render_template
import pandas as pd
from plot.Plot import plot_recent_order
from database.TradeHistory import get_engine

app = Flask(__name__)


@app.route('/')
def hello():
    return 'hello bitcoin trader'


@app.route('/order')
def result_all():
    content = plot_order()
    return render_template('result.html', title='order', item_list=content)


def plot_order():
    df = pd.read_sql("select * from orderdata where child_order_id='coincheck-order'", get_engine())
    html = plot_recent_order(df)
    content = [{
        'plot': html,
        'name': 'order',
    }]
    return content


if __name__ == '__main__':
    app.run(host='0.0.0.0')
