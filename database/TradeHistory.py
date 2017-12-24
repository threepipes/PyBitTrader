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


def get_engine():
    return create_engine('sqlite:///db.sqlite3')


def get_session():
    return sessionmaker(bind=get_engine())()


def init_db():
    Base.metadata.create_all(get_engine())