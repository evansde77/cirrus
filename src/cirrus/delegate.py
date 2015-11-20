#!/usr/bin/env python
"""
_delegate_

Main cirrus command that delegates the call to
the sub command verb enabling

git cirrus do_a_thing  to be routed to the appropriate
command call for do_a_thing

"""
import os
import os.path
import pkg_resources
import sys
import signal
import subprocess

import cirrus.environment as env


def install_signal_handlers():
    """
    Need to catch SIGINT to allow the command to be CTRL-C'ed

    """
    def signal_handler(signal, frame):
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)


def run_command(cmd):
    """
    run the delegated command with the CTRL-C signal handler
    in place
    """
    install_signal_handlers()
    return subprocess.call(cmd, shell=False)


HELP = \
"""
Cirrus commands available are:

{0}

Do git cirrus <command> -h for more information on a
particular command
"""


def format_help(command_list):
    subs = '\n'.join(
        [c for c in command_list if c != 'cirrus']
    )
    return HELP.format(subs)


def main():
    """
    _main_

    response to the cirrus <verb> command
    Extracts the available verbs that are installed as
    entry points by setup.py as cirrus_commands

    """
    home = env.virtualenv_home()
    commands = []
    for script in pkg_resources.iter_entry_points(group="cirrus_commands"):
        comm = str(script).split(" = ", 1)[0]
        commands.append(comm)
    commands.sort()

    # switch to the current GIT_PREFIX working dir
    old_dir = os.getcwd()
    os.chdir(os.path.abspath(os.environ.get('GIT_PREFIX', '.')))

    try:
        args = sys.argv[1:]
        if len(args) == 0 or args[0] == '-h':
            # missing command or help
            print format_help(commands)
            exit_code = 0
        else:
            command_path = "{0}/bin/{1}".format(home, args[0])
            if not os.path.exists(command_path):
                msg = "Unknown command: {}".format(args[0])
                print msg
                print format_help(commands)
                exit_code = 127
            else:
                exit_code = run_command([command_path, ] + args[1:])
    finally:
        # always return to previous dir
        os.chdir(old_dir)
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
