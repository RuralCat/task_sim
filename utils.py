
import datetime
import scipy.stats as st
import numpy as np

class Datetime(object):
    def __init__(self, year=2000, month=1, day=1, hour=0, minute=0):
        self.time = datetime.datetime(year, month, day, hour, minute)

    def timedelta(self, minutes):
        self.time += datetime.timedelta(minutes=minutes)


def datetime_time(date, time):
    assert isinstance(date, datetime.datetime)
    assert isinstance(time, datetime.time)
    return datetime.datetime(date.year, date.month, date.day,
                             time.hour, time.minute)

Task_Generation_Lamba = np.arange(24) + 2
PRINT_ID = ['id_{}'.format(i) for i in range(10)]

def print_task(id, processor_name, time, type='enter'):
    if id in PRINT_ID:
        print('task {} {} {} at {}'.format(id, type, processor_name, time))

if __name__ == '__main__':
    # dtime = Datetime(year=2000, month=1, day=1, hour=0, minute=0)
    day = datetime.datetime(2000, 1, 2).time()
    print(day)
