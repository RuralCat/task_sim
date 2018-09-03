
import datetime
import scipy.stats as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import MultipleLocator, FormatStrFormatter

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

def plot_graph(params, param_name, mean_time_l, completion_in24_rate_l,
               mean_os_work_time_l, mean_ss_work_time_l, save_path):
    plt.rcParams['font.sans-serif'] = ['Microsoft Yahei']

    title = "{}变化影响".format(param_name)
    xmajorLocator = MultipleLocator(1)  # 将x主刻度标签设置为1的倍数
    xmajorFormatter = FormatStrFormatter('%1.1f')  # 设置x轴标签文本的格式

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(params, mean_time_l, label="平均时效")
    ax1.plot(params, mean_ss_work_time_l, label='自营平均下班时间')
    ax1.plot(params, mean_os_work_time_l, label='外包平均下班时间')
    ax1.xaxis.set_major_locator(xmajorLocator)
    ax1.set_xlabel('{}'.format(param_name), fontsize=14)
    ax1.set_ylabel('时效/下班时间', fontsize=14)

    ax1.set_xlim([params[0], params[-1]])
    ax1.set_ylim([5, 26])
    ax1.legend(loc=4)

    ax2 = ax1.twinx()
    ax2.plot(params, completion_in24_rate_l, ':', label='24小时履约率')
    ax2.set_ylabel('24小时履约率', fontsize=14)
    ax2.set_ylim([0.5, 1.1])
    ax2.legend(loc=0)

    ax1.grid(True)
    #ax2.legend(loc=0)
    plt.title(title, fontsize=18) #fontproperties="Microsoft Yahei"
    plt.savefig(save_path)
    plt.show()


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
