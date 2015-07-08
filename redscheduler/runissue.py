from __future__ import print_function

import sys
import os.path
import shutil

import argparse

from redscheduler import config, scheduler

def parse_args():
    parser = argparse.ArgumentParser(
        'Runs issues'
    )

    parser.add_argument(
        'issueid',
        type=int,
        help='Issue Id of issue to run'
    )

    parser.add_argument(
        '--config',
        '-c',
        default=os.path.join(os.path.expanduser('~/'), '.redscheduler.config'),
        help='Config file to use[Default: %(default)s]'
    )

    parser.add_argument(
        '--rerun',
        default=False,
        action='store_true',
        help='Ovewrite existing output directory[Default: %(default)s]'
    )

    return parser.parse_args()

def main():
    args = parse_args()
    c = config.load_config(args.config)
    job = scheduler.RedScheduler(c).Job.get(args.issueid)
    if args.rerun:
        sys.stdout.write('Overwriting existing directory {0}\n'.format(
            job.issue_dir
        ))
        shutil.rmtree(job.issue_dir)
    if not os.path.exists(job.issue_dir):
        try:
            job.run()
        except Exception as e:
            job.notes = str(e)
            job.statusname = 'Error'
            job.save()
            raise e
    else:
        sys.stderr.write('Refusing to overwrite existing directory {0}\n'.format(
            job.issue_dir
        ))
        return 17
