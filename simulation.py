

from task import TaskGenerator, TaskStack, TaskProcessor, VoucherType, \
    InnerTaskProcessor, VoucherProcessor, ResultProcessor
from simpy import Environment
import numpy as np
import datetime as dt

if __name__ == '__main__':
    # create process environment
    env = Environment()
    tick = 0.5
    start_time = dt.time(0, 0)
    end_time = dt.time(0, 10)
    last_task_time = dt.time(0, 10)
    ss_capability = 11
    ss_process_time = 1.5
    os_capability = 60
    os_process_time = 2
    cs_process_time = 2
    run_time_days = 0
    run_time_hours = 0
    run_time_minutes = 10
    # create recorded data processor
    finished_proc = ResultProcessor(env, name='finished tasks', tick=tick)
    unfinished_proc = ResultProcessor(env, name='unfinished tasks', tick=tick)
    # creare self-support processor
    ss_proc = InnerTaskProcessor(env,
                                 name='ss_processor',
                                 tick=tick,
                                 capability=ss_capability,
                                 start_time=start_time,
                                 end_time=end_time,
                                 process_time=ss_process_time,
                                 down_processors=finished_proc,
                                 voucher_ratio=0.1,
                                 extend_working=True,
                                 last_task_time=last_task_time)
    # create ss voucher processot
    ss_voucher_proc = VoucherProcessor(env,
                                       name='ss_voucher_processor',
                                       tick=tick,
                                       down_processors=ss_proc,
                                       process_time_scale=1.0)
    ss_proc.voucher_processor = ss_voucher_proc
    # create outer sourcing processor
    os_proc = InnerTaskProcessor(env,
                                 name='os_processor',
                                 tick=tick,
                                 capability=os_capability,
                                 start_time=start_time,
                                 end_time=end_time,
                                 process_time=os_process_time,
                                 down_processors=[finished_proc, ss_proc],
                                 downweights=[0.59, 0.41],
                                 voucher_processor=None,
                                 voucher_ratio=0.4,
                                 extend_working=True,
                                 last_task_time=last_task_time)
    # create os voucher processor
    os_voucher_proc = VoucherProcessor(env,
                                       name='os_voucher_processor',
                                       tick=tick,
                                       down_processors=[os_proc, unfinished_proc],
                                       downweights=[0.5, 0.5],
                                       process_time_scale=1.0)
    os_proc.voucher_processor = os_voucher_proc
    # create crowd sourcing processor
    cs_proc = TaskProcessor(env,
                            name='cs_processor',
                            tick=tick,
                            start_time=start_time,
                            end_time=end_time,
                            process_time=cs_process_time,
                            down_processors=[os_proc, finished_proc],
                            downweights=[0.89, 0.11])
    # create task generator
    generator = TaskGenerator(env,
                              name='task_generator',
                              tick=1,
                              down_processors=[cs_proc, os_proc],
                              downweights=[0.69, 0.31])
    # ----------------- Run Process ----------------- #
    # create process
    env.process(generator.work())
    env.process(cs_proc.work())
    env.process(os_proc.work())
    env.process(os_voucher_proc.work())
    env.process(ss_proc.work())
    env.process(ss_voucher_proc.work())
    env.process(finished_proc.work())
    env.process(unfinished_proc.work())
    # run
    run_time = dt.timedelta(days=run_time_days,
                            hours=run_time_hours,
                            minutes=run_time_minutes).total_seconds() / 60
    env.run(until=run_time)
    #
    time_list = []
    for task in finished_proc.result_stack:
        time_list.append(task.time_consuming(['ss_voucher_processor', 'os_voucher_processor']))
        print(task.id, time_list[-1])
    total_time = dt.timedelta(0)
    for time in time_list:
        total_time += time
    print('mean time ', total_time / len(time_list))
