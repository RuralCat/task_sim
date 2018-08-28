

from simpy import Environment
import pandas as pd
import matplotlib.pyplot as plt

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
    param_l = np.arange(55,80,1)
    mean_time_l =  [8.93, 8.929, 8.641, 8.878, 8.778, 8.848, 8.78, 8.574, 8.736, 8.538, 8.63, 8.597, 8.745, 8.491, 8.373, 8.59, 8.67,
     8.672, 8.462, 8.508, 8.601, 8.475, 8.481, 8.403, 8.352]
    lvyue_rate_l = [0.992, 0.992, 0.995, 0.993, 0.991, 0.992, 0.994, 0.992, 0.993, 0.994, 0.994, 0.993, 0.993, 0.995, 0.996, 0.996,
     0.994, 0.993, 0.996, 0.994, 0.992, 0.993, 0.995, 0.995, 0.995]
    mean_os_work_time_l =  [18.1, 18.1, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0,
     18.0, 18.0, 18.0, 18.0, 18.0, 18.0]
    mean_ss_work_time_l = [20.0, 20.1, 20.0, 20.2, 20.0, 20.3, 20.3, 20.0, 20.1, 20.0, 20.1, 20.0, 20.2, 20.1, 19.9, 20.2, 20.4, 20.3, 20.1,
     20.4, 20.2, 20.1, 20.2, 20.1, 20.0]


    result = pd.merge(pd.merge(pd.merge(mean_time_l, lvyue_rate_l), pd.merge(mean_os_work_time_l, mean_ss_work_time_l)),param_l)
    title = "客服数量与理赔综合指标"
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.plot(param_l, mean_time_l)
    ax1.set_ylabel('mean_time_l')
    ax1.set_title("mean_time_l")

    ax2 = ax1.twinx()
    ax2.plot(param_l, lvyue_rate_l, 'r')
    ax2.set_ylabel('lvyue_rate_l')
    ax2.set_xlabel('lvyue_rate_l')

    ax1.grid(True)
    plt.title(title)
    plt.show()

