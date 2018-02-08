# coding: UTF-8
import os
import slackweb
from urllib.error import HTTPError
from utils.settings import get_logger

logger = get_logger()
WEBHOOK_URL = os.environ.get('MY_INC_URL', '')


def slack(message, channel='#bittrader'):
    sl = slackweb.Slack(url=WEBHOOK_URL)
    try:
        sl.notify(text=message, channel=channel)
    except HTTPError as e:
        logger.error('slack error')
        logger.exception(e)
