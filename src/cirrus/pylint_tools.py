#!/usr/bin/env python
"""
_pylint_tools_

Wrapper for pylint execution


"""

import os
import re
import sys
from fabric.operations import local, settings, hide

from cirrus.logger import get_logger

LOGGER = get_logger()

import pep8


def pylint_file(filenames, **kwargs):
    """
    apply pylint to the file specified,
    return the filename, score

    """
    command = "pylint "

    if 'rcfile' in kwargs and kwargs['rcfile'] is not None:
        command += " --rcfile={0} ".format(kwargs['rcfile'])

    command = command + ' '.join(filenames)

    # we use fabric to run the pylint command, hiding the normal fab
    # output and warnings
    with hide('output', 'running', 'warnings'), settings(warn_only=True):
        result = local(command, capture=True)

    score = 0.0
    # parse the output from pylint for the score
    for line in result.split('\n'):
        if  re.match("E....:.", line):
            LOGGER.info(line)
        if "Your code has been rated at" in line:
            score = re.findall("\d+.\d\d", line)[0]

    score = float(score)
    return filenames, score


def pyflakes_file(filenames, verbose=False):
    """
    _pyflakes_file_

    Appyly pyflakes to file specified,
    return (filenames, score)
    """
    command = 'pyflakes ' + ' '.join(filenames)

    # we use fabric to run the pyflakes command, hiding the normal fab
    # output and warnings
    with hide('output', 'running', 'warnings'), settings(warn_only=True):
        result = local(command, capture=True)

    flakes = 0
    data = [x for x in result.split('\n') if x.strip()]
    if len(data) != 0:
        #We have at least one flake, find the rest
        flakes = count_flakes(data, verbose) + 1
    else:
        flakes = 0

    return filenames, flakes


def count_flakes(data, verbose):
    """
    Helper function for finding additional flakes by counting
    line returns
    """
    additional_flakes = 0
    for line in data:
        if verbose:
            LOGGER.info(line)
        additional_flakes += 1

    return additional_flakes


def pep8_file(filenames, verbose=False):
    """
    _pep8_file_

    Run pep8 checker on a file, returning the filenames, score
    as a tuple
    """
    pep8style = pep8.StyleGuide(quiet=True)
    result = pep8style.check_files(filenames)
    if verbose:
        result.print_statistics()
    return filenames, result.total_errors
