from datetime import datetime
import logging as log
import subprocess
import time
from multiprocessing.pool import Pool


def magic_cpu_usage_increaser(period: int):
    start_time = time.time()
    print_time = time.time()
    while time.time() - start_time < period:
        if time.time() - print_time > 5:
            print_time = time.time()
            log.error('Thread stuck in kernel module for %s seconds, waiting for file descriptor to be released.'
                      'Too many open files.', period)
    log.error('Thread stuck in kernel module for %s seconds, waiting for file descriptor to be released.'
                      'Too many open files.', period)

def outage_start(period: int, threads: int, interval_days: int, start_date: datetime, interval_based_trigger: str):

    date_format = "%m/%d/%Y"
    if interval_based_trigger == 'false' or \
        (interval_based_trigger == 'true' and interval_days == 0) or \
        (interval_based_trigger == 'true' and interval_days != 0 and (datetime.strptime(datetime.now().strftime(date_format), date_format) - datetime.strptime(start_date.strftime(date_format), date_format)).days % interval_days == 0):
        log.info('Deploying new version 1.20.124')
        log.info('Upgrade initiated: admin mode by joe@sumocoffee.com')
        with Pool(threads) as p:
            p.map(magic_cpu_usage_increaser, [period])

        log.info('Deploying new version 1.20.123')
    else:
        log.info('Not yet time for the CPU trigger.')


def network_outage_start(delay: str, period: int, interval_days: int, start_date: datetime, interval_based_trigger: str):

    date_format = "%m/%d/%Y"
    if interval_based_trigger == 'false' or \
        (interval_based_trigger == 'true' and interval_days == 0) or \
        (interval_based_trigger == 'true' and interval_days != 0 and (datetime.strptime(datetime.now().strftime(date_format), date_format) - datetime.strptime(start_date.strftime(date_format), date_format)).days % interval_days == 0):

        subprocess.call(['tcset', 'eth0', '--delay', delay])

        time.sleep(period)

        subprocess.call(['tcdel', 'eth0', '--all'])
    else:
        log.info('Not yet time for the network trigger.')
