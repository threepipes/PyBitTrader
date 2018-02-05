from datetime import datetime as dt

time_format = '%Y-%m-%dT%H:%M:%S.%f'
time_format_nf = '%Y-%m-%dT%H:%M:%S.%f'


def date2str(dateobj: dt):
    return dateobj.strftime(time_format)


def str2date(tstr):
    # tstr = '2015-07-08T02:43:34.72'
    format = time_format if '.' in tstr else tstr
    tdatetime = dt.strptime(tstr, format)
    return tdatetime
