import os
import slackweb

WEBHOOK_URL = os.environ.get('MY_INC_URL', '')


def slack(message, channel='#sys-log'):
    sl = slackweb.Slack(url=WEBHOOK_URL)
    sl.notify(text=message, channel=channel)
