
from simpy import Environment
import numpy as np
from enum import Enum
import datetime as dt
from utils import Task_Generation_Lamba, print_task

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
        print_task(self.id, taskbase.name, taskbase.now.isoformat(), 'enter')

    def leave_processor(self, taskbase):
        # create time stamp
        self.time_stamps.append(TaskTimeStamp(taskbase))
        print_task(self.id, taskbase.name, taskbase.now.isoformat(), 'leave')

    def time_consuming(self, voucher_processor_name=None, with_voucher=False):
        # the time of task creation
        start_time = self.time_stamps[0].time
        # the time of task finish
        end_time = self.time_stamps[-1].time
        # voucher time
        voucher_time_list = []
        for stamp in self.time_stamps:
            if stamp.processor in voucher_processor_name:
                voucher_time_list.append(stamp.time)
        voucher_time = dt.timedelta(0)
        for i in range(np.int(len(voucher_time_list) / 2)):
            voucher_time += (voucher_time_list[2*i+1] - voucher_time_list[2*i])
        # time consuming
        if with_voucher:
            time_consuming = end_time - start_time
        else:
            time_consuming = end_time - start_time - voucher_time

        return time_consuming

class TaskStack(list):

    @property
    def task_count(self):
        return len(self)

    @property
    def is_empty(self):
        return True if self.task_count <= 0 else False

    def add_task(self, task):
        assert isinstance(task, Task)
        self.append(task)

    def pop_task(self):
        return self.pop(0)

class TaskBase(object):
    def __init__(self, env, name, tick):
        assert isinstance(env, Environment)
        self.env = env
        self.name = name
        self.tick = tick
        self._time = dt.datetime(2018, 1, 1)

    @property
    def now(self):
        return self._time

    @property
    def clock_time(self):
        return self._time.time()

    def time_update(self, minute=1):
        self._time += dt.timedelta(minutes=minute)

class TaskProcessor(TaskBase):
    def __init__(self, env, name,
                 tick=0.5,
                 capability=np.Inf,
                 start_time=dt.time(0, 0),
                 end_time=dt.time(23, 59),
                 process_time=0,
                 down_processors=[],
                 downweights=None):
        """
        :param env: simpy enviroment
        :param name: processor name used in time stamp
        :param tick: run 'work' function by tick
        :param capability: max size of working task stack
        :param start_time: the start working time of processor
        :param end_time: the stop working time of processor
        :param process_time: the process time for task in the processor
        :param down_processors: next stages for processed task
        :param downweights: list(number)
        """
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
            #if self.now.time() == self.start_time:
            #    print('cache size in {} is {}'.format(self.name, self.cache_taskstack.task_count))
            #if self.name == 'ns_processor':
            #    print(self.now, self.cache_taskstack.task_count, self.working_taskstack.task_count)
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
                while not self.cache_taskstack.is_empty and self.capable:
                    self._get_new_task()
            # update time
            yield self.env.timeout(self.tick)
            self.time_update(self.tick)

    def get_process_time(self):
        return self.process_time

    def _get_new_task(self):
        task = self.cache_taskstack.pop_task()
        task.enter_processor(self)
        self._add_new_task(task)
        return task

    def _add_new_task(self, task):
        self.working_taskstack.add_task(task)

    def _push_task_to_next_stage(self, task):
        self._tradition_push(task)

    def _tradition_push(self, task):
        # reset voucher to false when task go to next stage
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

class TaskGenerator(TaskProcessor):
    def __init__(self, env, name='task_generator', tick=1,
                 down_processors=[], downweights=None):
        TaskProcessor.__init__(self, env, name, tick,
                               down_processors=down_processors, downweights=downweights)
        self.task_count = 0

    def work(self):
        while True:
            # print rate of progress
            if self.now.time() == dt.time(0,0):
                print('current simulation time is {}'.format(self.now.date()))
            # generate new tasks
            tasks = self._get_new_task()
            for task in tasks:
                task.leave_processor(self)
                self._push_task_to_next_stage(task)
            # update time
            yield self.env.timeout(self.tick)
            self.time_update(self.tick)


    @property
    def next_task_num(self):
        hour = self.clock_time.hour
        lam = Task_Generation_Lamba[hour]
        return np.random.poisson(lam, size=1).__int__()

    def _get_new_task(self):
        # create new tasks
        new_tasks = TaskStack()
        for _ in range(self.next_task_num):
            self.task_count += 1
            id = 'id_{}'.format(self.task_count)
            task = Task(id)
            task.enter_processor(self)
            new_tasks.add_task(task)
        return new_tasks

    def _add_new_task(self, task):
        assert isinstance(task, TaskStack)
        for _ in range(task.task_count):
            self.working_taskstack.add_task(task.pop_task())

class InnerTaskProcessor(TaskProcessor):
    def __init__(self, env, name, tick=0.5, capability=np.Inf,
                 start_time=dt.time(0, 0), end_time=dt.time(23, 59),
                 process_time=0,
                 down_processors=[], downweights=None,
                 voucher_processor=None, voucher_ratio=0,
                 extend_working=False, last_task_time=dt.time(18,0)):
        TaskProcessor.__init__(self, env, name, tick, capability,
                               start_time, end_time, process_time,
                               down_processors, downweights)
        if voucher_processor is not None:
            assert isinstance(voucher_processor, VoucherProcessor)
        self.voucher_processor = voucher_processor
        self.voucher_ratio = voucher_ratio
        self.extend_working = extend_working
        self.last_task_time = last_task_time
        self.working_flag = False

    @property
    def working(self):
        working_flag = self.clock_time >= self.start_time and \
                       self.clock_time <= self.end_time
        if self.extend_working:
            working_flag = working_flag or not self.working_taskstack.is_empty
        return working_flag

    @property
    def capable(self):
        capable_flag = self.working_taskstack.task_count < self.capability
        if self.clock_time >= self.start_time and self.clock_time <= self.end_time:
            pass
        else:
            capable_flag = capable_flag and \
                           self.cache_taskstack[0].time_stamps[-1].time.time() < self.last_task_time
        return capable_flag

    def _get_new_task(self):
        task = self.cache_taskstack.pop_task()
        task.enter_processor(self)
        self._add_new_task(task)

    def _add_new_task(self, task):
        if self.extend_working and self.clock_time > self.last_task_time:
            t = task.time_stamps[-2].time.time()
            if t < self.last_task_time:
                self.working_taskstack.add_task(task)
        else:
            self.working_taskstack.add_task(task)

    def _push_task_to_next_stage(self, task):
        # determine voucher status
        if self.voucher_processor is not None and task.voucher == VoucherType.NOT_DETERMINED:
            if np.random.rand(1) < self.voucher_ratio:
                task.voucher = VoucherType.SUFFICIENT
            else:
                task.voucher = VoucherType.LACKED
        else:
            task.voucher = VoucherType.SUFFICIENT
        # push task into different branch according to voucher type
        if task.voucher == VoucherType.LACKED:
            self.voucher_processor.cache_taskstack.add_task(task)
        else:
            self._tradition_push(task)

class VoucherProcessor(TaskProcessor):
    def __init__(self, env, name, tick=0.5, down_processors=[], downweights=None, process_time_scale=1.0):
        TaskProcessor.__init__(self, env, name, tick,
                               down_processors=down_processors,
                               downweights=downweights)
        self.process_time_scale = process_time_scale

    def get_process_time(self):
        return np.random.exponential(self.process_time_scale, size=1)

class ResultProcessor(TaskProcessor):
    def __init__(self, env, name, tick=1):
        TaskProcessor.__init__(self, env, name, tick)
        self.result_stack = TaskStack()

    def work(self):
        while True:
            while not self.cache_taskstack.is_empty:
                task = self._get_new_task()
                self.result_stack.add_task(task)
            # update time
            yield self.env.timeout(self.tick)
            self.time_update(self.tick)

if __name__ == '__main__':
    env = Environment()
    new_tasks = TaskStack()
    gen = TaskGenerator(env, new_tasks)
    env.process(gen.generate())
    env.run(until=1)
    print(len(new_tasks))
