

from simpy import Environment
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import MultipleLocator, FormatStrFormatter


def clock(env, name, tick, num):
    assert isinstance(env, Environment)
    assert isinstance(num, list)
    while True:
        num.append(env.now)
        print(name, env.now)
        yield env.timeout(tick)


class Car(object):
    def __init__(self, env):
        self.env = env
        # Start the run process everytime an instance is created.
        self.action = env.process(self.run())

    def run(self):
        while True:
            print('Start parking and charging at %d' % self.env.now)
            charge_duration = 5
            # We yield the process that process() returns
            # to wait for it to finish
            yield self.env.process(self.charge(charge_duration))

            # The charge process has finished and
            # we can start driving again.
            print('Start driving at %d' % self.env.now)
            trip_duration = 2
            yield self.env.timeout(trip_duration)

    def charge(self, duration):
        yield self.env.timeout(duration)

if __name__ == '__main__':
    param_l = np.arange(15, 35, 1)
    mean_time_l = [15.58, 15.181, 14.88, 14.622, 14.137, 13.612, 13.268, 12.966, 12.629, 12.315, 12.058, 11.78, 11.472, 11.394, \
                   11.338, 11.209, 11.225, 11.256, 11.223, 11.224]
    completion_in24_rate_l = [0.823, 0.848, 0.873, 0.895, 0.946, 0.974, 0.988, 0.997, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    mean_os_work_time_l = [18.2, 18.2, 18.2, 18.3, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2, 18.2]
    mean_ss_work_time_l = [24.0, 23.9, 23.7, 22.9, 22.2, 21.4, 20.8, 20.3, 19.9, 19.4, 19.0, 18.6, 18.3, 18.2, 18.1, 18.0, 18.0, 18.0, 18.0, 18.0]

    plt.rcParams['font.sans-serif'] = ['Microsoft Yahei']

    title = "自营人数变化影响"
    xmajorLocator = MultipleLocator(1)  # 将x主刻度标签设置为1的倍数
    xmajorFormatter = FormatStrFormatter('%1.1f')  # 设置x轴标签文本的格式

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(param_l, mean_time_l, label = "平均时效")
    ax1.plot(param_l, mean_ss_work_time_l, label = '自营平均下班时间')
    ax1.xaxis.set_major_locator(xmajorLocator)
    ax1.set_xlabel('自营人数',fontsize=14)
    ax1.set_ylabel('时效/下班时间',fontsize=14)

    ax1.set_xlim([10, 16])
    ax1.set_ylim([5, 26])
    ax1.legend(loc=4)

    ax2 = ax1.twinx()
    ax2.plot(param_l, completion_in24_rate_l, ':',label = '24小时履约率')
    ax2.set_ylabel('24小时履约率',fontsize=14)
    ax2.set_ylim([0.5, 1.1])
    ax2.legend(loc=0)

    ax1.grid(True)
    #ax2.legend(loc=0)
    plt.title(title,fontsize=18) #fontproperties="Microsoft Yahei"
    plt.show()

