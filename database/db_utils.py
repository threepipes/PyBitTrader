from sqlalchemy import desc
import pandas as pd
import datetime

from database.TradeHistory import History


def get_recent_query(data_type, n, session):
    return session.query(data_type).order_by(desc(data_type.id)).limit(n)


def get_recent_df(data_type, n, session):
    statement = get_recent_query(data_type, n, session).statement
    return pd.read_sql(statement, session.bind)


def get_recent_hist_query(from_time, session):
    return session.query(History).filter(History.exec_date > from_time)


def avg(p, n):
    return p.rolling(n).mean()


def std(p, n):
    return p.rolling(n).std()


def zs(p, n):
    return (p - p.rolling(n).mean()) / p.rolling(n).std()


def history2indicator(df):
    # Historyデータを方針決定用のデータに変換
    df.exec_date = pd.to_datetime(df.exec_date)
    df = df.set_index('exec_date')
    df = df.loc['2000':]
    df = df[['id', 'price', 'size']]

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
    # rや前の行動を保持しないといけない問題
    for r_label in ['r', 'r_1', 'r_2']:
        dfb[r_label] = 0
    dfb['state'] = 0

    dfb['pZ12'] = zs(p, 12)
    dfb['pZ96'] = zs(p, 96)
    dfb['vol12'] = zs(std(p, 12), 96)
    dfb['vol96'] = zs(std(p, 96), 96)
    dfb['vol672'] = zs(std(p, 672), 96)
    dfb['dv12_96'] = zs(std(p, 12) / avg(std(p, 12), 96), 96)
    dfb['dv96_672'] = zs(std(p, 96) / avg(std(p, 96), 672), 96)

    indicator = dfb.reset_index().loc[:, 'pma12':'dv96_672']
    price_history = dfb.reset_index().price

    return price_history, indicator