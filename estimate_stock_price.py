#!/usr/bin/env python3
from argparse import ArgumentParser
from datetime import date
from os import getcwd
from subprocess import run, check_call, CalledProcessError, Popen, PIPE
from sys import exit
import re

r_log = re.compile('^.*app:(.*)$')

APP_ENV_FILE = 'app.env'
APP_SERVICE_NAME = 'app'

def print_command(args):
    command = ' '.join(args)
    print(f"Running {command}")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('symbol',
                        type=lambda sym: sym if 0 < len(sym) <= 5 else False,
                        help="Stock listing to model for")
    parser.add_argument('date',
                        type=date.fromisoformat,
                        help="Predict stock's price at <yyyy-mm-dd>")
    args = parser.parse_args()

    with open(APP_ENV_FILE, 'w') as env_file:
        env_file.write(f"APP_SYMBOL={args.symbol}\n")
        env_file.write(f"APP_DATE={args.date.isoformat()}\n")

    current_dir = getcwd()

    run_args = ['docker-compose', 'up', '-d', '--no-deps', APP_SERVICE_NAME]
    print_command(run_args)
    try:
        start_job = run(args=run_args, cwd=current_dir, check=True)
    except CalledProcessError as e:
        exit(e.returncode)

    log_args = ['docker-compose', 'logs', '-f', '--no-color', APP_SERVICE_NAME]
    print_command(log_args)
    logs = Popen(args=log_args, cwd=current_dir, stdout=PIPE, stderr=PIPE)
    try:
        while True:
            exit_code = logs.poll()
            if exit_code == None:
                out = logs.stdout.readline().decode('utf-8')
                match = r_log.match(out)
                if match:
                    msg = match.group(1)
                    print(msg)
            else:
                exit(exit_code)
    except KeyboardInterrupt:
        stop_args = ['docker-compose', 'stop', APP_SERVICE_NAME]
        print_command(stop_args)
        run(args=stop_args, cwd=current_dir)
