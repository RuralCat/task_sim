

from task import TaskGenerator, TaskStack, TaskProcessor, VoucherType, \
    InnerTaskProcessor, VoucherProcessor, ResultProcessor
from simpy import Environment
import numpy as np
import datetime as dt
import pandas as pd
import time

SIMULATION_ATTRS = ['tick', 'start_time', 'end_time', 'last_task_time', 'ss_capability',
                 'ss_process_time', 'os_capability', 'os_process_time', 'cs_process_time',
                 'run_time_days', 'extend_working', 'create_cnt', 'create_cancel', 'create_cs',
                 'create_os', 'create_ss', 'cs_finish', 'cs_os', 'os_voucher', 'os_voucher_os',
                 'os_finish_ss', 'ss_voucher', 'ss_voucher_ss']

class Simulation(object):
    def __init__(self, save_path, show_logging=True, init_paras_from_text=True):
        # create process environment
        self.env = Environment()
        # define paras
        if init_paras_from_text:
            self.__init_paras_fomr_text()
        else:
            self.tick = 0.5 #模拟时间步长，单位 分钟
            self.start_time = dt.time(9, 0) # 上班时间
            self.end_time = dt.time(18, 0) # 下班时间
            self.last_task_time = dt.time(18, 0) # 接收的最后工作时间
            self.ss_capability = 11 # 自营人数
            self.ss_process_time = 1.5 # 自营处理一个任务需要的分钟
            self.os_capability = 88 # 外包人数
            self.os_process_time = 2 # 外包处理一个任务需要的分钟
            self.cs_process_time = 120 # 众包处理一个任务需要的时间
            self.run_time_days = 15 # 模拟天数
            self.extend_working = True # 是否加班
            self.create_cnt = 16000  # 工单创建量
            self.create_cancel = 0.02 # 创建_剔除
            self.create_cs = 0.79 # 创建剔除_众包
            self.create_os = 0.20 # 创建剔除_外包
            self.create_ss = 0.01 # 创建剔除_自营
            self.cs_finish = 0.10 # 众包_完结
            self.cs_os = 0.90 # 众包_外包
            self.os_voucher = 0.40 # 外包_凭证
            self.os_voucher_os = 0.43 # 外包凭证_返回
            self.os_finish_ss = 0.59 # 外包完结_自营
            self.ss_voucher = 0.16 # 自营_凭证
            self.ss_voucher_ss = 0.91 # 自营凭证_返回

        self.run_time_hours = 0  # 模拟小时数
        self.run_time_minutes = 0  # 模拟分钟数
        # create processors
        self.processors = {}
        self._create_processors()
        # save path
        self.save_path = save_path
        self.show_logging = show_logging

    def set_param(self, name, value):
        if hasattr(self, name):
            self.__setattr__(name, value)
            self.env = Environment()
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
                                         voucher_ratio=self.ss_voucher,  #自营补传凭证比例
                                         extend_working=self.extend_working,
                                         last_task_time=self.last_task_time)
        # create ss voucher processot
        self.ss_voucher_proc = VoucherProcessor(self.env,
                                                name='ss_voucher_processor',
                                                tick=self.tick,
                                                down_processors=[self.ss_proc, self.unfinished_proc],
                                                downweights=[self.ss_voucher_ss, 1-self.ss_voucher_ss], #凭证返回比例
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
                                     downweights=[1-self.os_finish_ss, self.os_finish_ss], #外包半智能完结比例
                                     voucher_processor=None,
                                     voucher_ratio=self.os_voucher, #外包补传凭证占比
                                     extend_working=self.extend_working,
                                     last_task_time=self.last_task_time)
        # create os voucher processor
        self.os_voucher_proc = VoucherProcessor(self.env,
                                           name='os_voucher_processor',
                                           tick=self.tick,
                                           down_processors=[self.os_proc, self.unfinished_proc],
                                           downweights=[self.os_voucher_os, 1-self.os_voucher_os], #外包补传凭证的上传概率
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
                                downweights=[1-self.cs_finish, self.cs_finish]) #众包完结流入外包占比
        # create task generator
        self.generator = TaskGenerator(self.env,
                                  name='task_generator',
                                  tick=1,
                                  down_processors=[self.cs_proc, self.os_proc,self.ss_proc],
                                  downweights=[self.create_cs, self.create_os,1-self.create_cs-self.create_os],#自营流入众包、外包、自营占比
                                  create_cnt=self.create_cnt,# 创建量
                                  create_cancel = self.create_cancel)#创建后直接取消比例

    def __init_paras_from_text(self):
        # read setting
        _, words = read_setting()
        values = []
        for word in words[:-4]:
            values.append(float(word))
        # set setting to simulation
        for value, attr in zip(values, SIMULATION_ATTRS):
            if attr in ['start_time', 'end_time', 'last_task_time']:
                hour = np.int(value)
                minute = np.int((value - hour) * 60)
                self.__setattr__(attr, dt.time(hour, minute))
            else:
                self.__setattr__(attr, value)

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
        # get result task stack
        res_taskstack = self.finished_proc.result_stack
        # get each task type and time consuming
        time_list = []
        type_list = []
        for task in res_taskstack:
            time_list.append(task.time_consuming(['ss_voucher_processor', 'os_voucher_processor']))
            type_list.append(task.time_stamps[-2].processor)
        # reject the first two
        if len(time_list) > 2:
            time_list = time_list[2:]
            type_list = type_list[2:]
        # compute mean time consuming & completion rate in time
        total_time = dt.timedelta(0)
        completion_in24_rate = 0
        intime_condition = {'cs_processor': 23.5, 'os_processor' : 20.2, 'ss_processor' : 22.4}
        system_time = {'cs_processor': 0.5, 'os_processor' : 3.8, 'ss_processor' : 1.6}
        for time, finish_type in zip(time_list, type_list):
            total_time = total_time + time + dt.timedelta(hours = system_time[finish_type])
            completion_in24_rate += np.int(time < dt.timedelta(hours=intime_condition[finish_type]))
        mean_time = round(total_time.total_seconds()/ 3600 / len(time_list), 3)
        completion_in24_rate = round(completion_in24_rate / len(time_list), 3)
        # get work time
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
        # reject the first two
        if len(os_work_time) > 2:
            os_work_time = os_work_time[2:-1]
            ss_work_time = ss_work_time[2:-1]
        # compute mean work time
        os_work_tt = 0
        ss_work_tt = 0
        for i in range(len(os_work_time)):
            os_work_tt += os_work_time[i].hour + os_work_time[i].minute / 60
            ss_work_tt += ss_work_time[i].hour + ss_work_time[i].minute / 60
        mean_os_work_time = round(os_work_tt / len(os_work_time), 1)
        mean_ss_work_time = round(ss_work_tt / len(ss_work_time), 1)

        return mean_time, completion_in24_rate, os_work_time, ss_work_time, mean_os_work_time, mean_ss_work_time

    def save_logging(self, name='', value=''):
        with open(self.save_path, 'a') as f:
            st = '{}: {}'.format(name, value)
            f.write(st + '\n')
            if self.show_logging: print(st)

    def save_default_attr(self):
        self.save_logging('default parameters', '')
        for attr in SIMULATION_ATTRS:
            if hasattr(self, attr):
                self.save_logging(attr, self.__getattribute__(attr))
        self.save_logging()

    def _get_work_time(self, taskstack):
        work_time = []
        current_day = taskstack[0].time_stamps[-2].time.date()
        for i in range(taskstack.task_count):
            day = taskstack[i].time_stamps[-2].time.date()
            if day > current_day:
                current_day = day
                work_time.append(taskstack[i - 1].time_stamps[-2].time.time())

        return work_time

def read_setting(setting_path='setting.txt'):
    # read text to parse setting
    attr_name = []
    words = []
    with open('setting.txt', 'r') as fid:
        lines = fid.readlines()
        for line in lines:
            attr_name.append(line.split('=')[0].replace(' ', ''))
            words.append(line.split('=')[1].split('#')[0].replace(' ', ''))
    return attr_name, words

if __name__ == '__main__':
    # define paras
    bread_setting = True
    mean_time_l = []
    completion_in24_rate_l = []
    mean_os_work_time_l = []
    mean_ss_work_time_l = []
    os_capabilitys = np.arange(85, 90, 1)
    ss_capabilitys = np.arange(15, 20, 1)

    # set adjustable parameter
    if bread_setting:
        attr_names, words = read_setting()
        params = np.arange(float(words[-3]), float(words[-2]), float(words[-1]))
        index = attr_names.index(words[-4])
        param_name = SIMULATION_ATTRS[index]
    else:
        params = ss_capabilitys
        param_name = 'ss_capability'
    # set save path
    lt = time.localtime(time.time())
    lt = '{}{}{}{}{}'.format(lt.tm_year, lt.tm_mon, lt.tm_mday, lt.tm_hour, lt.tm_min)
    save_path = 'simulation_{}_{}_from{}to{}.txt'.format(lt, param_name, params[0], params[-1])
    # create simulation
    sim = Simulation(save_path, init_paras_from_text=bread_setting)
    # save params
    sim.save_default_attr()
    sim.save_logging('Adjustable Parameter', param_name)
    sim.save_logging('Adjustable Range', params)
    sim.save_logging()
    # loop by params
    for param in params:
        # show param
        sim.save_logging('current {}'.format(param_name), param)
        # set param
        sim.set_param(param_name, param)
        # run
        sim.run()
        # get analysis information
        mean_time, completion_in24_rate,os_work_time, ss_work_time, \
        mean_os_work_time, mean_ss_work_time = sim.logging()
        # save to list
        mean_time_l.append(mean_time)
        completion_in24_rate_l.append(completion_in24_rate)
        mean_os_work_time_l.append(mean_os_work_time)
        mean_ss_work_time_l.append(mean_ss_work_time)
        # save logging
        sim.save_logging('mean task aging', mean_time)
        sim.save_logging('task completion rate in 24 hours', completion_in24_rate)
        sim.save_logging('outer sourcing work time', os_work_time)
        sim.save_logging('self supporting work time', ss_work_time)
        sim.save_logging('mean outer sourcing work time', mean_os_work_time)
        sim.save_logging('mean self supporting work time', mean_ss_work_time)
        sim.save_logging()
    # save list
    sim.save_logging('list res')
    sim.save_logging('mean task aging list', mean_time_l)
    sim.save_logging('task completion rate list', completion_in24_rate_l)
    sim.save_logging('mean outer sourcing work time list', mean_os_work_time_l)
    sim.save_logging('mean self supporting work time list', mean_ss_work_time_l)
    # plot

