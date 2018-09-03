
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

def plot_graph():
    pass


Task_Generation_Distribution = np.array([0.012, 0.004, 0.002, 0.001, 0.001, 0.002,
                                         0.009, 0.022, 0.037, 0.059, 0.075, 0.080,
                                         0.072, 0.060, 0.055, 0.067, 0.074, 0.070,
                                         0.061, 0.053, 0.054, 0.057, 0.048, 0.026])
OMIT_TIME = [12]

PRINT_ID = ['id_{}'.format(i) for i in range(0)]

def print_task(id, processor_name, time, type='enter'):
    if id in PRINT_ID:
        print('task {} {} {} at {}'.format(id, type, processor_name, time))

if __name__ == '__main__':
    # dtime = Datetime(year=2000, month=1, day=1, hour=0, minute=0)
    day = datetime.datetime(2000, 1, 2).time()
    task_num = np.sum(Task_Generation_Lamba * 60)
    print(1800 * 10)
    print(task_num * 0.93)
