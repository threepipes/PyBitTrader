from sqlalchemy import desc
import pandas as pd

from database.TradeHistory import History, History15min


def get_recent_query(data_type, n, session):
    return session.query(data_type).order_by(desc(data_type.id)).limit(n)


def get_recent_df(data_type, n, session):
    statement = get_recent_query(data_type, n, session).statement
    return pd.read_sql(statement, session.bind)


def get_recent_hist_query(from_time, session):
    return session.query(History).filter(History.exec_date > from_time)


def get_recent_hist_df(from_time, session):
    statement = get_recent_hist_query(from_time, session).statement
    return pd.read_sql(statement, session.bind)


def get_recent_hist15_query(from_time, session):
    return session.query(History15min).filter(History15min.exec_date > from_time)


def get_recent_hist15_df(from_time, session):
    statement = get_recent_hist15_query(from_time, session).statement
    return pd.read_sql(statement, session.bind)


def set_dateindex(df):
    df.exec_date = pd.to_datetime(df.exec_date)
    return df.set_index('exec_date')


def avg(p, n):
    return p.rolling(n).mean()


def std(p, n):
    return p.rolling(n).std()


def zs(p, n):
    return (p - p.rolling(n).mean()) / p.rolling(n).std()
