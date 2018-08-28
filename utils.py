
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

Task_Generation_Lamba = np.array([153, 59, 28, 16, 13, 28, 123,
                                  288, 487, 780, 991, 1058, 954,
                                  795, 729, 886, 985,933, 811, 701,
                                  713, 752, 634, 351]) / 60
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
