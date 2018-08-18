
from simpy import Environment
import numpy as np
from enum import Enum
import datetime as dt
from utils import Task_Generation_Lamba
from simulation import InnerTaskProcessor

class TaskTimeStamp(object):
    def __init__(self, taskbase, process_time=None):
        assert isinstance(taskbase, TaskBase)
        self.processor = taskbase.name
        self.time = taskbase.now
        if process_time is not None:
            self.process_time = process_time
        else:
            self.process_time = -1
class VoucherType(Enum):
    NOT_DETERMINED = 0
    LACKED = 1
    SUFFICIENT = 2
    SUPPLEMENTARY = 3

class Task(object):
    def __init__(self, id):
        self.id = id
        self.task_type = 0
        self.time_stamps = []
        self._process_time = 0
        self._processed_time = 0
        self.voucher = VoucherType.NOT_DETERMINED

    @property
    def Processed(self):
        return self._processed_time >= self._process_time

    def update_processed_time(self, tick):
        self._processed_time += tick

    def enter_processor(self, taskbase):
        if isinstance(taskbase, TaskProcessor):
            process_time = taskbase.get_process_time()
        else:
            process_time = None
        # set process time in current processor
        self._process_time = process_time
        # create time stamp
        self.time_stamps.append(TaskTimeStamp(taskbase, process_time))
        # init processed time
        self._processed_time = 0
        # reset vouvher if needed
        if isinstance(taskbase, InnerTaskProcessor) and self.voucher == VoucherType.SUFFICIENT:
            self.voucher = VoucherType.NOT_DETERMINED

    def leave_processor(self, taskbase):
        # create time stamp
        self.time_stamps.append(TaskTimeStamp(taskbase))

class TaskBase(object):
    def __init__(self, env, name, tick):
        assert isinstance(env, Environment)
        self.env = env
        self.name = name
        self.tick = tick
        self._time = dt.datetime(2000, 1, 1)

    @property
    def now(self):
        return self._time

    @property
    def clock_time(self):
        return self._time.time()

    def time_update(self, minute=1):
        self._time += dt.timedelta(minutes=minute)

class TaskGenerator(TaskProcessor):
    def __init__(self, env, name='task_generator', tick=1,
                 down_processors=[], downweights=None):
        TaskProcessor.__init__(self, env, name, tick,
                               down_processors=down_processors, downweights=downweights)

    @property
    def next_task_num(self):
        hour = self.clock_time.hour
        lam = Task_Generation_Lamba[hour]
        return np.random.poisson(lam, size=1)

    def _get_new_task(self):
        # create new tasks
        new_tasks = TaskStack()
        for _ in range(self.next_task_num):
                id = 'id_'.format(self.new_tasks.task_count)
                task = Task(id)
                task.enter_processor()
                new_tasks.add_task(task)
        return new_tasks

    def _add_new_task(self, task):
        assert isinstance(task, TaskStack)
        for _ in range(task.task_count):
            self.working_taskstack.add_task(task.pop_task())

class TaskStack(list):

    @property
    def task_count(self):
        return len(self)

    @property
    def is_empty(self):
        return True if self.task_count == 0 else False

    def add_task(self, task):
        assert isinstance(task, Task)
        self.append(task)

    def pop_task(self):
        return self.pop(0)

class TaskProcessor(TaskBase):
    def __init__(self, env, name, tick=0.5, capability=np.Inf,
                 start_time=dt.time(0, 0), end_time=dt.time(23, 59), process_time=0,
                 down_processors=[], downweights=None):
        TaskBase.__init__(self, env, name, tick)
        self.capability = capability
        self.start_time = start_time
        self.end_time = end_time
        self.process_time = process_time
        # create taskstack link
        if isinstance(down_processors, list):
            for processor in down_processors:
                assert isinstance(processor, TaskProcessor)
        else:
            assert isinstance(down_processors, TaskProcessor)
        self.cache_taskstack = TaskStack()
        self.down_processors = down_processors
        self.down_weights = downweights
        # create working task stack
        self.working_taskstack = TaskStack()

    @property
    def working(self):
        return self.clock_time >= self.start_time and \
               self.clock_time <= self.end_time

    @property
    def capable(self):
        return self.working_taskstack.task_count < self.capability

    def work(self):
        while True:
            # run this work function evety 1 time unit
            # process in work time
            if self.working:
                # push the completed task into next stage
                if not self.working_taskstack.is_empty:
                    for _ in range(self.working_taskstack.task_count):
                        task = self.working_taskstack.pop_task()
                        task.update_processed_time(self.tick)
                        if task.Processed:
                            task.leave_processor(self)
                            self._push_task_to_next_stage(task)
                        else:
                            self._add_new_task(task)
                # get new task if processor is capable
                while self.capable:
                    if self.cache_taskstack.task_count == 0:
                        break
                    else:
                        task = self._get_new_task()
                        self._add_new_task(task)
            # update time
            yield self.env.timeout(self.tick)
            self.time_update(self.tick)

    def get_process_time(self):
        return self.process_time

    def _get_new_task(self):
        task = self.cache_taskstack.pop_task()
        task.enter_processor()
        return task

    def _add_new_task(self, task):
        self.working_taskstack.add_task(task)

    def _push_task_to_next_stage(self, task):
        self.__tradition_push(task)

    def _tradition_push(self, task):
        # reset voucher to false when task go to next stage
        task.voucher = False
        if isinstance(self.down_processors, TaskProcessor):
            self.down_processors.cache_taskstack.add_task(task)
        else:
            if self.down_weights:
                weights = np.cumsum(np.array(self.down_weights))
                rand_seed = np.random.rand(1)
                ind = np.nonzero(rand_seed < weights)[0][0]
                self.down_processors[ind].cache_taskstack.add_task(task)
            else:
                raise ValueError('down weights should not be None')


if __name__ == '__main__':
    env = Environment()
    new_tasks = TaskStack()
    gen = TaskGenerator(env, new_tasks)
    env.process(gen.generate())
    env.run(until=10)
    print(len(new_tasks))
