
import datetime

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

if __name__ == '__main__':
    # dtime = Datetime(year=2000, month=1, day=1, hour=0, minute=0)
    dtime = Datetime()
    dtime.timedelta(10)
    a = dtime
    a.timedelta(20)
    a = datetime.datetime(2000, 1, 1)
    b = a
    a = a + datetime.timedelta(minutes=20)
    print(a)
    print(b)