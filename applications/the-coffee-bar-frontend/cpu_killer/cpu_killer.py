import asyncio
import logging as log
import subprocess
import sys
import time
from datetime import datetime, timedelta
from multiprocessing.pool import Pool
from os import getenv

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.util import undefined
from cron_descriptor import get_description


def magic_cpu_usage_increaser(period: int):
    start_time = time.time()
    while time.time() - start_time < period:
        pass


def outage_start(period: int, threads: int, interval_days: int, start_date: datetime, interval_based_trigger: str):

    date_format = "%m/%d/%Y"
    if interval_based_trigger == 'false' or \
        (interval_based_trigger == 'true' and interval_days == 0) or \
        (interval_based_trigger == 'true' and (datetime.strptime(datetime.now().strftime(date_format), date_format) - datetime.strptime(start_date.strftime(date_format), date_format)).days % interval_days == 0):

        log.info('Increasing CPU Usage - threads=%d' % threads)
        with Pool(threads) as p:
            p.map(magic_cpu_usage_increaser, [period])
    else:
        log.info('Not yet time for CPU Spike.')


def network_outage_start(delay: str, period: int, interval_days: int, start_date: datetime, interval_based_trigger: str):

    date_format = "%m/%d/%Y"
    if interval_based_trigger == 'false' or \
        (interval_based_trigger == 'true' and interval_days==0) or \
        (interval_based_trigger == 'true' and (datetime.strptime(datetime.now().strftime(date_format), date_format) - datetime.strptime(start_date.strftime(date_format), date_format)).days % interval_days == 0):
        log.info('Adding network delay: %s' % delay)
        subprocess.call(['tcset', 'eth0', '--delay', delay])

        time.sleep(period)

        log.info('Removing network delay')
        subprocess.call(['tcdel', 'eth0', '--all'])
    else:
        log.info('Not yet time for Network Spike.')


root = log.getLogger()
root.setLevel(log.INFO)
root.name = 'cpu_killer'

span_formattter = log.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

stdout_handler = log.StreamHandler(sys.stdout)
stdout_handler.setLevel(log.INFO)
stdout_handler.setFormatter(span_formattter)
root.addHandler(stdout_handler)

loop = asyncio.get_event_loop()
try:
    cpu_spike_processes = int(getenv('CPU_SPIKE_PROCESSES')) if getenv('CPU_SPIKE_PROCESSES') is not None else 475
    spike_duration = int(getenv('SPIKE_DURATION')) if getenv('SPIKE_DURATION') is not None else 60
    network_delay_time = str(getenv('NETWORK_DELAY')) if getenv('NETWORK_DELAY') is not None else '1sec'
    spike_start_date = str(getenv('SPIKE_START_DATE'))
    start_date_datetime = undefined
    interval_based_trigger = str(getenv('INTERVAL_BASED_TRIGGER')) if getenv('INTERVAL_BASED_TRIGGER') is not None else 'false'
    spike_interval_hours = 1
    spike_interval_days = 0
    start_date_datetime_interval = datetime.now() + timedelta(hours = spike_interval_hours)

    scheduler = BackgroundScheduler()

    if interval_based_trigger == 'true':
        spike_interval_days = int(getenv('SPIKE_INTERVAL_DAYS')) if getenv('SPIKE_INTERVAL_DAYS') is not None else 0
        spike_interval_hours = int(getenv('SPIKE_INTERVAL_HOURS')) if getenv('SPIKE_INTERVAL_HOURS') is not None else 1
        start_date_datetime_interval = datetime.now() + timedelta(hours = spike_interval_hours)
        trigger = IntervalTrigger(hours=spike_interval_hours)
    else:
        cron = str(getenv('SPIKE_CRON')) if getenv('SPIKE_CRON') is not None else '0 * * * *'
        trigger = CronTrigger.from_crontab(cron)
        log.info('SPIKE CRON %s' % get_description(cron))

    try:
        if spike_start_date is not None:
            start_date_datetime = datetime.strptime(spike_start_date, '%Y-%m-%d %H:%M:%S')
            start_date_datetime_interval = start_date_datetime
    except:
        log.info('Invalid Date Format for CRON start date.')

    scheduler.add_job(outage_start, trigger, [spike_duration, cpu_spike_processes, spike_interval_days, start_date_datetime_interval, interval_based_trigger],
                      next_run_time=start_date_datetime)
    scheduler.add_job(network_outage_start, trigger, [network_delay_time, spike_duration, spike_interval_days, start_date_datetime_interval, interval_based_trigger],
                      next_run_time=start_date_datetime)

    if spike_duration > 0:
        log.info('CPU KILLER enabled')
        log.info('SPIKE START DATE %s' % start_date_datetime)
        log.info('CPU SPIKE PROCESSES %d' % cpu_spike_processes)
        log.info('SPIKE DURATION (s) %d' % spike_duration)
        log.info('NETWORK DELAY %s' % network_delay_time)
        log.info('CRON START DATE %s', start_date_datetime)
        scheduler.start()
        loop.run_forever()
    else:
        log.info('CPU/NETWORK KILLER disabled')
finally:
    loop.close()
