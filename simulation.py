

from task import TaskGenerator, TaskStack, TaskProcessor
from simpy import Environment
import numpy as np
import datetime as dt

class InnerTaskProcessor(TaskProcessor):
    def __init__(self, env, name, capability=np.Inf,
                 start_time=dt.time(0, 0), end_time=dt.time(23, 59),
                 process_time=0,
                 top_taskstack=[], down_taskstacks=[], downweights=None,
                 voucher_taskstack=None, voucher_ratio=0,
                 extend_working=False, last_task_time=dt.time(18,0)):
        TaskProcessor.__init__(self, env, name, capability,
                               start_time, end_time, process_time,
                               top_taskstack, down_taskstacks, downweights)
        self.voucher_taskstack= voucher_taskstack
        self.voucher_ratio = voucher_ratio
        self.extend_working = extend_working
        self.last_task_time = last_task_time

    @property
    def working(self):
        working_flag = self.clock_time >= self.start_time and \
                       self.clock_time <= self.end_time
        if self.extend_working:
            working_flag = working_flag or \
                           self.working_taskstack.task_count > 0
        return working_flag

    def _add_new_task(self, task):
        if self.extend_working:
            t = task.time_stamps[-1]['time']
            if t < self.last_task_time:
                self._add_new_task(task)
        else:
            self._add_new_task(task)

    def _push_task_to_next_stage(self, task):
        if self.voucher_taskstack and not task.voucher:
            if np.random.rand(1) < self.voucher_ratio:
                task.voucher = True
            if not task.voucher:
                self.voucher_taskstack.add_task(task)
            else:
                self._tradition_push(task)
        else:
            self._tradition_push(task)


class VoucherProcessor(object):
    def __init__(self):
        pass

if __name__ == '__main__':
    # create process environment
    env = Environment()
    start_time = dt.time(9, 0)
    end_time = dt.time(18, 0)
    # create task generator
    new_taskstack = TaskStack()
    generator = TaskGenerator(env, new_taskstack)
    # first distribution processor
    cs_taskstack = TaskStack()
    sc_taskstack = TaskStack()
    distribution_processor = TaskProcessor(env,
                                           name='distribution',
                                           capability=np.Inf,
                                           start_time=start_time,
                                           end_time=end_time,
                                           process_time=0,
                                           top_taskstack=new_taskstack,
                                           down_taskstacks=[cs_taskstack,
                                                            sc_taskstack],
                                           downweights=[0.69, 0.31])
    # create crowd sourcing processor
    cs_processor = TaskProcessor(env,
                                 name='crowd_sourcing',
                                 capability=np.Inf,)