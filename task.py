
from simpy import Environment
import numpy as np
from enum import Enum
import datetime as dt
from utils import datetime_time

class TaskType(Enum):
    """
    CS - crowd sourcing
    SC - subcontract
    SS - self-support
    """

class Task(object):
    def __init__(self, id):
        self.id = id
        self.task_type = 0
        self.time_stamps = []
        self.process_time = []
        self.voucher = False

    def add_task_stamp(self, taskbase):
        assert isinstance(taskbase, TaskBase)
        self.time_stamps.append({'processor' : taskbase.name,
                                 'time' : taskbase.now})

    def set_process_time(self, taskproc):
        assert isinstance(taskproc, TaskProcessor)
        self.process_time.append({'processor' : taskproc.name,
                                 'time' : taskproc.get_process_time()})

    def to_next_stage(self, current_time, start_time, end_time):
        """
        current_time:
        process_time: process time in current stage (unit in minute)
        :return: bool result
        """
        if len(self.time_stamps) > 0:
            assert isinstance(current_time, dt.datetime)
            assert isinstance(start_time, dt.time)
            assert isinstance(end_time, dt.time)
            enter_stage_time = self.time_stamps[-1]['time']
            if current_time.day == enter_stage_time.day:
                if current_time.time() > end_time:
                    processed_time = datetime_time(current_time, end_time) - enter_stage_time
                else:
                    processed_time = current_time - enter_stage_time
            else:
                if current_time.time() < start_time:
                    processed_time = dt.timedelta()
                else:
                    processed_time = current_time - enter_stage_time
                    delta_seconds = (start_time.hour + 24 - end_time.hour) * 3600 + \
                                    (start_time.minute - end_time.minute) * 60
                    processed_time -= dt.timedelta(seconds=delta_seconds)

            return processed_time.total_seconds() >= self.process_time[-1]['time'] * 60
        else:
            raise ValueError('the task has no time stamp')

class TaskBase(object):
    def __init__(self, env, name):
        assert isinstance(env, Environment)
        self.env = env
        self.name = name
        self._time = dt.datetime(2000, 1, 1)

    @property
    def now(self):
        return self._time

    @property
    def clock_time(self):
        return self._time.time()

    def time_update(self, minute=1):
        self._time += dt.timedelta(minutes=minute)


class TaskGenerator(TaskBase):
    def __init__(self, env, new_tasks, name='task_generator'):
        assert isinstance(new_tasks, TaskStack)
        TaskBase.__init__(self, env, name)
        self.new_tasks = new_tasks

    def generate(self):
        while True:
            # create a new task
            id = 'id_'.format(self.now)
            task = Task(id, self.now, self.name)
            task.add_task_stamp(self)
            self.new_tasks.add_task(task)
            # wait next task
            yield self.env.timeout(1)
            self.time_update(1)

    @property
    def next_task_time(self):
        return 1

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
    def __init__(self, env, name, capability=np.Inf,
                 start_time=dt.time(0, 0), end_time=dt.time(23, 59),
                 process_time=0,
                 top_taskstack=[], down_taskstacks=[], downweights=None):
        TaskBase.__init__(self, env, name)
        self.capability = capability
        self.start_time = start_time
        self.end_time = end_time
        self.process_time = process_time
        # create taskstack link
        assert isinstance(top_taskstack, TaskStack)
        if isinstance(down_taskstacks, list):
            for taskstack in down_taskstacks:
                assert isinstance(taskstack, TaskStack)
        else:
            assert isinstance(down_taskstacks, TaskStack)
        self.top_taskstack = top_taskstack
        self.down_taskstacks = down_taskstacks
        self.down_weights = downweights
        # create working task stack
        self.working_taskstack = TaskStack()

    @property
    def working(self):
        return self.clock_time > self.start_time and \
               self.clock_time < self.end_time

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
                        process_time = self.get_process_time()
                        if task.to_next_stage(self.now, process_time):
                            self._push_task_to_next_stage(task)
                        else:
                            self._add_new_task(task)
                # get new task if processor is capable
                while self.capable:
                    if self.top_taskstack.task_count == 0:
                        break
                    else:

                        self._add_new_task(task)
            # update time
            yield self.env.timeout(0.5)
            self.time_update(0.5)

    def get_process_time(self):
        return self.process_time

    def _add_new_task(self, task):
        task = self.top_taskstack.pop_task()
        task.add_task_stamp(self)
        self.working_taskstack.add_task(task)

    def _push_task_to_next_stage(self, task):
        task.add_task_stamp(self)
        self.__tradition_push(task)

    def _tradition_push(self, task):
        # reset voucher to false when task go to next stage
        task.voucher = False
        if isinstance(self.down_taskstacks, TaskStack):
            self.down_taskstacks.add_task(task)
        else:
            if self.down_weights:
                weights = np.cumsum(np.array(self.down_weights))
                rand_seed = np.random.rand(1)
                ind = np.nonzero(rand_seed < weights)[0][0]
                self.down_taskstacks[ind].add_task(task)
            else:
                raise ValueError('down weights should not be None')


if __name__ == '__main__':
    env = Environment()
    new_tasks = TaskStack()
    gen = TaskGenerator(env, new_tasks)
    env.process(gen.generate())
    env.run(until=10)
    print(len(new_tasks))
    dt.timedelta
    np.random.rand()
