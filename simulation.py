

from task import TaskGenerator, TaskStack, TaskProcessor, VoucherType, \
    InnerTaskProcessor, VoucherProcessor, ResultProcessor
from simpy import Environment
import numpy as np
import datetime as dt

class Simulation(object):
    def __init__(self):
        # create process environment
        self.env = Environment()
        # define paras
        self.tick = 0.5 # 模拟时间步长，单位 分钟
        self.start_time = dt.time(9, 0) # 上班时间
        self.end_time = dt.time(18, 0) # 下班时间
        self.last_task_time = dt.time(18, 0) # 接收的最后工作时间
        self.ss_capability = 11 # 自营人数
        self.ss_process_time = 1.5 # 自营处理一个任务需要的时间
        self.os_capability = 60 # 外包人数
        self.os_process_time = 2 # 外包处理一个任务需要的时间
        self.cs_process_time = 240 # 众包处理一个任务需要的时间
        self.run_time_days = 30 # 模拟天数
        self.run_time_hours = 0 # 模拟小时数
        self.run_time_minutes = 10 # 模拟分钟数
        self.extend_working = True # 是否加班
        # create processors
        self.processors = {}
        self._create_processors()

    def _create_processors(self):
        # create recorded data processor
        self.finished_proc = ResultProcessor(self.env,
                                             name='finished tasks',
                                             tick=self.tick)
        self.unfinished_proc = ResultProcessor(self.env,
                                               name='unfinished tasks',
                                               tick=self.tick)
        # creare self-support processor
        self.ss_proc = InnerTaskProcessor(self.env,
                                         name='ss_processor',
                                         tick=self.tick,
                                         capability=self.ss_capability,
                                         start_time=self.start_time,
                                         end_time=self.end_time,
                                         process_time=self.ss_process_time,
                                         down_processors=self.finished_proc,
                                         voucher_ratio=0.1,
                                         extend_working=self.extend_working,
                                         last_task_time=self.last_task_time)
        # create ss voucher processot
        self.ss_voucher_proc = VoucherProcessor(self.env,
                                           name='ss_voucher_processor',
                                           tick=self.tick,
                                           down_processors=self.ss_proc,
                                           process_time_scale=1.0)
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
                                     downweights=[0.59, 0.41],
                                     voucher_processor=None,
                                     voucher_ratio=0.4,
                                     extend_working=self.extend_working,
                                     last_task_time=self.last_task_time)
        # create os voucher processor
        self.os_voucher_proc = VoucherProcessor(self.env,
                                           name='os_voucher_processor',
                                           tick=self.tick,
                                           down_processors=[self.os_proc, self.unfinished_proc],
                                           downweights=[0.5, 0.5],
                                           process_time_scale=1.0)
        self.os_proc.voucher_processor = self.os_voucher_proc
        # create crowd sourcing processor
        self.cs_proc = TaskProcessor(self.env,
                                name='cs_processor',
                                tick=self.tick,
                                start_time=self.start_time,
                                end_time=self.end_time,
                                process_time=self.cs_process_time,
                                down_processors=[self.os_proc, self.finished_proc],
                                downweights=[0.89, 0.11])
        # create task generator
        self.generator = TaskGenerator(self.env,
                                  name='task_generator',
                                  tick=1,
                                  down_processors=[self.cs_proc, self.os_proc],
                                  downweights=[0.69, 0.31])

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
        for time in time_list:
            total_time += time
        mean_time = total_time / len(time_list)
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

        return mean_time, os_work_time, ss_work_time

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
    sim = Simulation()
    sim.run()
    mean_time, os_work_time, ss_work_time = sim.logging()
    print(mean_time)
    print(os_work_time)
    print(ss_work_time)
