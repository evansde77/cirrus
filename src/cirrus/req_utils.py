#!/usr/bin/env python
"""
reqs_utils

Tools for assisting with requirements files

"""
import re

#
# use pip ops to parse file
#
PIP_OPERATORS = [
    "~=",
    "==",
    "!=",
    "<=",
    ">=",
    ">",
    "<",
    "==="
]

REGEXP = "(^[\w\-]+[ ]*[{op}]{{1}})"

RE_OPERATORS = re.compile("|".join([
    REGEXP.format(op=op) for op in PIP_OPERATORS
]))

SPLIT_OPS = {
    op: re.compile("({op}){{1}}".format(op=op))
    for op in PIP_OPERATORS
}


def find_operator(d):
    if all(x is None for x in d.values()):
        return None
    ops = [k for k, v in d.items() if v is not None]
    if len(ops) == 1:
        return ops[0]
    # lazily grab longest key
    return max(ops)


class ReqFile(dict):
    """
    wrapper for a requirements file to provide a basic
    API for simple edits like version bumps, listing packages
    etc

    """
    def __init__(self, filename):
        super(ReqFile, self).__init__(self)
        self.filename = filename
        self.operators = {}

    def read(self):
        with open(self.filename, 'r') as handle:
            content = handle.read()
            for line in content.split():
                yield line

    def parse(self):
        for line in self.read():
            if line.strip():
                self.process_line(line)

    def process_line(self, line):
        if RE_OPERATORS.match(line):
            op = find_operator({
                o: matcher.search(line) for o, matcher in SPLIT_OPS.items()
            })
            pkg = line.split(op, 1)[0]
            self[pkg] = line.split(op, 1)[1]
            self.operators[pkg] = op
        else:
            pkg = line
            self[pkg] = None
            self.operators[pkg] = None

    def has_package(self, pkg):
        return pkg in self

    def package_has_version(self, pkg):
        return self.get(pkg) is not None

    def bump(self, pkg, version):
        """
        bump the version of package in the requirements file

        """
        if not self.has_package(pkg):
            msg = "Unable to find package {} in file {}".format(
                pkg,
                self.filename
            )
            raise KeyError(msg)

        if self.operators.get(pkg) is not None:
            replacer = re.compile("^[\s]*({pkg}){{1}}[\s]*({op}){{1}}".format(
                pkg=pkg,
                op=self.operators[pkg])
            )
        else:
            replacer = re.compile("^[\s]*({pkg}){{1}}$".format(pkg=pkg))
        output = []
        for line in self.read():
            if replacer.match(line.strip()):
                op = self.operators[pkg] or '=='
                line = "{pkg}{op}{version}".format(
                    pkg=pkg,
                    op=op,
                    version=version
                )
                output.append(line)
            else:
                output.append(line)
        with open(self.filename, 'w') as handle:
            for line in output:
                handle.write('{}\n'.format(line))
        self.parse()


def bump_package(requirements_file, package, version):
    """
    given a path to a requirements file, find the package entry in it
    and bump the dependency version to the specified value
    modifies the existing requirements file.
    """
    rf = ReqFile(requirements_file)
    rf.parse()
    rf.bump(package, version)
