# coding: UTF-8
import os
from sqlalchemy import Column, String, Float, DateTime, Integer, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext import declarative
import datetime

Base = declarative.declarative_base()


class Border(Base):
    __tablename__ = 'border'

    id = Column(Integer, primary_key=True)
    buy_line = Column(Float)
    sell_line = Column(Float)
    price = Column(Integer)
    timestamp = Column(DateTime)

    def __repr__(self):
        return '<Border: price=%s b=%s s=%s>' % (
            self.price, self.buy_line, self.sell_line
        )

    @classmethod
    def create(cls, price, buy, sell, timestamp=None):
        if not timestamp:
            timestamp = datetime.datetime.today()
        return Border(**{
            'price': price,
            'buy_line': buy,
            'sell_line': sell,
            'timestamp': timestamp
        })


class Order(Base):
    __tablename__ = 'orderdata'

    id = Column(Integer, primary_key=True)
    product_code = Column(String(10))
    side = Column(String(4))
    price = Column(Integer)
    size = Column(Float)
    child_order_type = Column(String(10))
    child_order_id = Column(String(50))
    minute_to_expire = Column(Integer)
    timestamp = Column(DateTime)

    def __repr__(self):
        return '<Order: %s %s price=%s size=%s>' % (
            self.product_code, self.side, self.price, self.size
        )

    @classmethod
    def create(cls, order, child_order_id, timestamp=None):
        if not timestamp:
            timestamp = datetime.datetime.today()
        order['timestamp'] = timestamp
        order['child_order_id'] = child_order_id
        return Order(**order)


class History(Base):
    __tablename__ = 'history'

    id = Column(Integer, primary_key=True)
    side = Column(String(4))
    price = Column(Integer)
    size = Column(Float)
    exec_date = Column(DateTime)
    buy_child_order_acceptance_id = Column(String(50))
    sell_child_order_acceptance_id = Column(String(50))

    def __repr__(self):
        return '<History: %s %s price=%s size=%s>' % (
            self.id, self.side, self.price, self.size
        )


class History15min(Base):
    __tablename__ = 'history15min'

    exec_date = Column(DateTime, primary_key=True)
    price = Column(Integer)
    size = Column(Float)

    def __repr__(self):
        return '<History15min: %s price=%s size=%s>' % (
            self.exec_date, self.price, self.size
        )


class History5min(Base):
    __tablename__ = 'history5min'

    exec_date = Column(DateTime, primary_key=True)
    price = Column(Integer)
    size = Column(Float)

    def __repr__(self):
        return '<History5min: %s price=%s size=%s>' % (
            self.exec_date, self.price, self.size
        )


def get_engine():
    user_name = os.getenv('TRADER_DB_USER', '')
    db_name = os.getenv('TRADER_DB', '')
    password = os.getenv('TRADER_DB_PASS', '')
    return create_engine('mysql+mysqlconnector://%s:%s@localhost/%s' % (
        user_name, password, db_name
    ))


def get_session():
    return sessionmaker(bind=get_engine())()


def init_db():
    Base.metadata.create_all(get_engine())