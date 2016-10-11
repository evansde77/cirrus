#!/usr/bin/env python
"""
_utils_

General purpose utils

"""
import codecs


def update_file(filename, sentinel, text):
    """
    _update_file_

    Replace a sentinel in the specified file with
    the text provided.

    If filename contains

    "
    REPLACEME

    Other text
    "

    Then calling this method with sentinel=REPLACEME, text="new text"
    will edit the file and produce content:

    "
    REPLACEME

    new text

    Other text
    "

    """
    content = None
    with codecs.open(filename, 'r', encoding='utf-8') as handle:
        content = handle.read()

    replacement = u"{0}\n\n{1}".format(sentinel, text)
    content = content.replace(sentinel, replacement, 1)
    with codecs.open(filename, 'w', encoding='utf-8') as handle:
        handle.write(content)
    return


def update_version(filename, new_version, vers_attr='__version__'):
    """
    _update_version_

    Util to update the __version__ field (or different if supplied)
    in a file with the new version string provided.

    Will append the version line if not found

    """
    lines = []
    with open(filename, 'r') as handle:
        lines = handle.readlines()

    updated = False
    for lineno, line in enumerate(lines):
        if line.startswith(vers_attr):
            lines[lineno] = "{0} = \"{1}\"\n".format(vers_attr, new_version)
            updated = True
            break
    if not updated:
        lines.append("{0} = \"{1}\"\n".format(vers_attr, new_version))

    with open(filename, 'w') as handle:
        handle.writelines(lines)
