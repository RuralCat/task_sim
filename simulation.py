

from task import TaskGenerator, TaskStack, TaskProcessor, VoucherType, \
    InnerTaskProcessor, VoucherProcessor, ResultProcessor
from simpy import Environment
import numpy as np
import datetime as dt
import pandas as pd

class Simulation(object):
    def __init__(self):
        # create process environment
        self.env = Environment()
        # define paras
        self.tick = 0.5 #模拟时间步长，单位 分钟
        self.start_time = dt.time(9, 0) # 上班时间
        self.end_time = dt.time(18, 0) # 下班时间
        self.last_task_time = dt.time(18, 0) # 接收的最后工作时间
        self.ss_capability = 11 # 自营人数
        self.ss_process_time = 1.5 # 自营处理一个任务需要的分钟
        self.os_capability = 60 # 外包人数
        self.os_process_time = 2 # 外包处理一个任务需要的分钟
        self.cs_process_time = 120 # 众包处理一个任务需要的时间
        self.run_time_days = 3 # 模拟天数
        self.run_time_hours = 0 # 模拟小时数
        self.run_time_minutes = 0 # 模拟分钟数
        self.extend_working = True # 是否加班
        # create processors
        self.processors = {}
        self._create_processors()

    def set_param(self, name, value):
        if hasattr(self, name):
            self.__setattr__(name, value)
            self._create_processors()
        else:
            raise AttributeError('simulation do not has this attribution')

    def _create_processors(self):
        # create recorded data processor
        self.finished_proc = ResultProcessor(self.env,
                                             name='finished tasks',
                                             tick=self.tick)
        self.unfinished_proc = ResultProcessor(self.env,
                                               name='unfinished tasks',
                                               tick=self.tick)
        # create self-support processor
        self.ss_proc = InnerTaskProcessor(self.env,
                                         name='ss_processor',
                                         tick=self.tick,
                                         capability=self.ss_capability,
                                         start_time=self.start_time,
                                         end_time=self.end_time,
                                         process_time=self.ss_process_time,
                                         down_processors=self.finished_proc,
                                         voucher_ratio=0.16,  #自营补传凭证比例
                                         extend_working=self.extend_working,
                                         last_task_time=self.last_task_time)
        # create ss voucher processot
        self.ss_voucher_proc = VoucherProcessor(self.env,
                                                name='ss_voucher_processor',
                                                tick=self.tick,
                                                down_processors=[self.ss_proc, self.unfinished_proc],
                                                downweights=[0.91, 0.09],
                                                process_time_scale=1/1542) #自营凭证补传平均时间分钟
        self.ss_proc.voucher_processor = self.ss_voucher_proc
        # create outer sourcing processor
        self.os_proc = InnerTaskProcessor(self.env,
                                     name='os_processor',
                                     tick=self.tick,
                                     capability=self.os_capability,
                                     start_time=self.start_time,
                                     end_time=self.end_time,
                                     process_time=self.os_process_time,
                                     down_processors=[self.finished_proc, self.ss_proc],
                                     downweights=[0.57, 0.43], #外包半智能完结占比
                                     voucher_processor=None,
                                     voucher_ratio=0.4, #外包补传凭证占比
                                     extend_working=self.extend_working,
                                     last_task_time=self.last_task_time)
        # create os voucher processor
        self.os_voucher_proc = VoucherProcessor(self.env,
                                           name='os_voucher_processor',
                                           tick=self.tick,
                                           down_processors=[self.os_proc, self.unfinished_proc],
                                           downweights=[0.43, 0.57], #外包补传凭证的上传概率
                                           process_time_scale=1/2505) #外包补传凭证平均时间分钟
        self.os_proc.voucher_processor = self.os_voucher_proc
        # create crowd sourcing processor
        self.cs_proc = TaskProcessor(self.env,
                                name='cs_processor',
                                tick=self.tick,
                                start_time=self.start_time,
                                end_time=self.end_time,
                                process_time=self.cs_process_time,
                                down_processors=[self.os_proc, self.finished_proc],
                                downweights=[0.90, 0.10]) #众包完结流入外包占比
        # create task generator
        self.generator = TaskGenerator(self.env,
                                  name='task_generator',
                                  tick=1,
                                  down_processors=[self.cs_proc, self.os_proc,self.ss_proc],
                                  downweights=[0.79, 0.20,0.01])#自营流入众包、外包、自营占比

    @property
    def run_time(self):
        return dt.timedelta(days=self.run_time_days,
                            hours=self.run_time_hours,
                            minutes=self.run_time_minutes).total_seconds() / 60

    def run(self):
        # ----------------- Run Process ----------------- #
        # create process
        self.env.process(self.generator.work())
        self.env.process(self.cs_proc.work())
        self.env.process(self.os_proc.work())
        self.env.process(self.os_voucher_proc.work())
        self.env.process(self.ss_proc.work())
        self.env.process(self.ss_voucher_proc.work())
        self.env.process(self.finished_proc.work())
        self.env.process(self.unfinished_proc.work())
        # run
        self.env.run(until=self.run_time)

    def logging(self):
        # compute mean time consuming
        time_list = []
        res_taskstack = self.finished_proc.result_stack
        for task in res_taskstack:
            time_list.append(task.time_consuming(['ss_voucher_processor', 'os_voucher_processor']))
        total_time = dt.timedelta(0)
        lvyue_cnt = 0
        for time in time_list:
            total_time += time
            if time <= dt.timedelta(hours=24):
                lvyue_cnt += 1
        mean_time = round(total_time.total_seconds()/ 3600 / len(time_list),3)
        lvyue_rate = round(lvyue_cnt / len(time_list),3)
        # compute mean work time
        os_res = TaskStack()
        ss_res = TaskStack()
        while not res_taskstack.is_empty:
            task = res_taskstack.pop_task()
            name = task.time_stamps[-2].processor
            if name == 'os_processor':
                os_res.add_task(task)
            elif name == 'ss_processor':
                ss_res.add_task(task)
        os_work_time = self._get_work_time(os_res)
        ss_work_time = self._get_work_time(ss_res)
        os_work_tt = 0
        ss_work_tt = 0
        for i in range(len(os_work_time)):
            os_work_tt += os_work_time[i].hour + os_work_time[i].minute/60
            ss_work_tt += ss_work_time[i].hour + ss_work_time[i].minute / 60
        mean_os_work_time = round(os_work_tt / len(os_work_time),1)
        mean_ss_work_time = round(ss_work_tt / len(os_work_time),1)

        return mean_time, lvyue_rate,os_work_time, ss_work_time, mean_os_work_time, mean_ss_work_time

    def _get_work_time(self, taskstack):
        work_time = []
        current_day = taskstack[0].time_stamps[-2].time.date()
        for i in range(taskstack.task_count):
            day = taskstack[i].time_stamps[-2].time.date()
            if day > current_day:
                current_day = day
                work_time.append(taskstack[i - 1].time_stamps[-2].time.time())

        return work_time


if __name__ == '__main__':
    mean_time_l = []
    lvyue_rate_l = []
    mean_os_work_time_l = []
    mean_ss_work_time_l = []
    os_capabilitys = np.arange(55,80,1)

    # set adjustable parameter
    params = os_capabilitys
    param_name = 'os_capability'
    # loop by params
    for param in params:
        # create simulation
        sim = Simulation()
        # show param
        print('Simulation: {} is {}'.format(param_name, param))
        # set param
        sim.set_param(param_name, param)
        # run
        sim.run()
        # logging
        mean_time, lvyue_rate,os_work_time, ss_work_time, \
        mean_os_work_time, mean_ss_work_time = sim.logging()
        mean_time_l.append(mean_time)
        lvyue_rate_l.append(lvyue_rate)
        print(mean_time)
        print(lvyue_rate)
        print(os_work_time)
        print(ss_work_time)
        mean_os_work_time_l.append(mean_os_work_time)
        mean_ss_work_time_l.append(mean_ss_work_time)
        print(mean_os_work_time)
        print(mean_ss_work_time)
    print(mean_time_l)
    print(lvyue_rate_l)
    print(mean_os_work_time_l)
    print(mean_ss_work_time_l)
