#!/usr/bin/env python2.7
"""
_bootstrap_

cirrus python bootstrap script invoked by the bash installer script

"""
import os
import json
import getpass


def ask_question(question, default=None, valid=None):
    """
    _ask_question_

    Ask a question on stdin

    """
    to_ask = "{0}".format(question)
    if default is not None:
        to_ask += " [{0}]: ".format(default)
    else:
        to_ask += ": "
    result = raw_input(to_ask)
    if result.strip() == '':
        if default is not None:
            result = default
        else:
            msg = "No response provided for question"
            print msg
            raise RuntimeError(msg)
    if valid is not None:
        if result not in valid:
            msg = "Invalid input: {0} must be one of {1}".format(
                result, valid
            )
            print msg
            raise RuntimeError(msg)
    return result


def read_gitconfig():
    gitconfig = os.path.join(os.environ['HOME'], '.gitconfig')
    with open(gitconfig, 'r') as handle:
        content = handle.read()

    if "[cirrus]" in content:
        pass


def main():
    """main installer call"""
    github_username = ask_question('what is your github username?', default=os.environ['USER'])
    #install_dir = ask_question('where should we install cirrus?', default=os.path.join(os.environ['HOME'], '.cirrus'))
    #github_pass = getpass.getpass('what is your github password?')
    #read_gitconfig()

if __name__ == '__main__':
    main()