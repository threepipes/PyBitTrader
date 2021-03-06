# coding: UTF-8
import os
from logging import getLogger, basicConfig, DEBUG

app_name = 'pybittrader'
env = os.getenv('PYBITTRADER_ENV', 'debug')


def logging_config():
    if env == 'debug':
        basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
    else:
        basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='log.txt')
    app_logger = getLogger(app_name)
    app_logger.setLevel(DEBUG)


def get_logger():
    return getLogger(app_name)
