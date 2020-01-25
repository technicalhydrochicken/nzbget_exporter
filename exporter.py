#!/usr/bin/env python3
import sys
import argparse
import os
import requests
import logging
import time
from prometheus_client import Gauge, start_http_server


def parse_args():
    """Parse the arguments."""
    parser = argparse.ArgumentParser(description="Export NZBGet metrics")
    parser.add_argument("-v",
                        "--verbose",
                        help="Be verbose",
                        action="store_true",
                        dest="verbose")

    return parser.parse_args()


def get_required_env(env_name):
    """Look up and return an environmental variable, or fail if not found."""
    if env_name not in os.environ:
        logging.error(("Oops, looks like you haven't set %s, please do that"
                       " and then try running the script again\n") % env_name)
        sys.exit(2)
    else:
        return os.environ[env_name]


def main():
    _ = parse_args()
    username = get_required_env('NZBGET_USERNAME')
    password = get_required_env('NZBGET_PASSWORD')
    url = get_required_env('NZBGET_URL')

    debug = os.environ.get('NZBGET_DEBUG', False)
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    start_http_server(8999)

    download_rate = Gauge('download_rate_bytes', 'Description of gauge')
    thread_count = Gauge('thread_count', 'Thread Count')
    up_time_seconds = Gauge('up_time_seconds', 'Seconds servers has been up')
    download_time_seconds = Gauge('download_time_seconds',
                                  'Seconds servers has been downloading')
    remaining_size = Gauge('remaining_size_bytes',
                           'Remaining size of all entries in download queue')
    forced_size = Gauge('forced_size_bytes',
                        'Remaining size of entries with FORCE priority')
    downloaded_size = Gauge('downloaded_size_bytes',
                            'Amount of data downloaded since server start')
    article_cache = Gauge('article_cache_bytes',
                          'Current usage of article cache')
    post_job_count = Gauge(
        'post_job_count',
        'Number of Par-Jobs or Post-processing script jobs in the post-processing queue (including current file)'
    )

    while True:

        logging.debug(f"Querying {url}")
        r = requests.get(f"{url}/jsonrpc/status", auth=(username, password))
        res = (r.json()['result'])

        download_rate.set(res['DownloadRate'])
        logging.debug(f"Got a download rate of {res['DownloadRate']}")
        thread_count.set(int(res['ThreadCount']))
        up_time_seconds.set(int(res['UpTimeSec']))
        download_time_seconds.set(int(res['DownloadTimeSec']))
        remaining_size.set(res['RemainingSizeMB'] * 1024)
        forced_size.set(res['ForcedSizeMB'] * 1024)
        downloaded_size.set(res['DownloadedSizeMB'] * 1024)
        article_cache.set(res['ArticleCacheMB'] * 1024)
        post_job_count.set(res['PostJobCount'])

        time.sleep(30)

    return 0


if __name__ == "__main__":
    sys.exit(main())
