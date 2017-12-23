from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DatetimeTickFormatter
from bokeh.plotting import figure
from datetime import datetime
from math import radians
from pytz import timezone


def get_data():
    return None


def update_data():
    now = datetime.now(tz=timezone("Asia/Tokyo"))
    new_data = dict(x=[now], y=[get_data()])
    source.stream(new_data, rollover=200)

#データソースの作成
source = ColumnDataSource(dict(x=[], y=[]))

#グラフの作成
fig = figure(x_axis_type="datetime",
             x_axis_label="Datetime",
             y_axis_label="Last Trade",
             plot_width=800,
             plot_height=600)
fig.title.text = "Bitcoin Charts"
fig.line(source=source, x="x", y="y", line_width=2, alpha=.85, color="blue")
fig.circle(source=source, x="x", y="y", line_width=2, color="blue")

#軸の設定
format = "%Y-%m-%d-%H-%M-%S"
fig.xaxis.formatter = DatetimeTickFormatter(
    seconds=[format],
    minsec =[format],
    minutes=[format],
    hourmin=[format],
    hours  =[format],
    days   =[format],
    months =[format],
    years  =[format]
)
fig.xaxis.major_label_orientation=radians(90)

#コールバックの設定
curdoc().add_root(fig)
curdoc().add_periodic_callback(update_data, 3000) #ms単位
