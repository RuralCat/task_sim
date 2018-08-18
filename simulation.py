

from task import TaskGenerator, TaskStack, TaskProcessor, VoucherType, \
    InnerTaskProcessor, VoucherProcessor, ResultProcessor
from simpy import Environment
import numpy as np
import datetime as dt

if __name__ == '__main__':
    # create process environment
    env = Environment()
    start_time = dt.time(9, 0)
    end_time = dt.time(18, 0)
    # create recorded data processor
    finished_proc = ResultProcessor(env, name='finished tasks')
    unfinished_proc = ResultProcessor(env, name='unfinished tasks')
    # create task generator
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