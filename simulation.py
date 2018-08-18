

from task import TaskGenerator, TaskStack, TaskProcessor, VoucherType, \
    InnerTaskProcessor, VoucherProcessor, ResultProcessor
from simpy import Environment
import numpy as np
import datetime as dt

if __name__ == '__main__':
    # create process environment
    env = Environment()
    start_time = dt.time(0, 0)
    end_time = dt.time(0, 5)
    last_task_time = dt.time(0, 10)
    # create recorded data processor
    finished_proc = ResultProcessor(env, name='finished tasks', tick=0.5)
    unfinished_proc = ResultProcessor(env, name='unfinished tasks', tick=0.5)
    # create outer sourcing processor
    os_proc = InnerTaskProcessor(env,
                                 name='os_processor',
                                 tick=0.5,
                                 capability=2,
                                 start_time=start_time,
                                 end_time=end_time,
                                 process_time=1.5,
                                 down_processors=finished_proc,
                                 downweights=None,
                                 voucher_processor=None,
                                 voucher_ratio=0,
                                 extend_working=True,
                                 last_task_time=last_task_time)
    # create crowd sourcing processor
    cs_proc = TaskProcessor(env,
                            name='cs_processor',
                            tick=0.5,
                            start_time=start_time,
                            end_time=end_time,
                            process_time=2,
                            down_processors=[os_proc, finished_proc],
                            downweights=[0.89, 0.11])
    # create task generator
    generator = TaskGenerator(env,
                              name='task_generator',
                              tick=1,
                              down_processors=[cs_proc, os_proc],
                              downweights=[0.69, 0.31])
    # first distribution processor

    # create crowd sourcing processor

    # ----------------- Run Process ----------------- #
    env.process(generator.work())
    env.process(cs_proc.work())
    env.process(os_proc.work())
    env.process(finished_proc.work())
    # run time
    env.run(until=10)
