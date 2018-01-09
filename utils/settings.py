from logging import getLogger, basicConfig, DEBUG

app_name = 'pybittrader'


def logging_config():
    basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
    app_logger = getLogger(app_name)
    app_logger.setLevel(DEBUG)


def get_logger():
    return getLogger(app_name)
