cirrus
======

python library build, test and devop like things assistant

[![Build Status](https://travis-ci.org/evansde77/cirrus.svg?branch=develop)](https://travis-ci.org/evansde77/cirrus)

Installation Prerequisites
==========================

* Cirrus requires either python/pip/virtualenv or conda and has been tested with python2.7, 3.5 and 3.6 as of Release 0.2.0. 
   * Since python3 support and conda support are fairly new, please report any problems as Issues in this project. 
* Git tools are heavily used, git is a requirement as cirrus is accessed via git command aliases.

Documentation
=============

Expanded Docs are available on the [Package Wiki](https://github.com/evansde77/cirrus/wiki)

Installation as a user:
=======================

```bash
curl -O https://raw.githubusercontent.com/evansde77/cirrus/develop/installer.sh
bash installer.sh
```

Or if you are using anaconda:

```bash
curl -O https://raw.githubusercontent.com/evansde77/cirrus/develop/conda-installer.sh
bash conda-installer.sh
```

See the 

Installation for Development:
=============================

_Note_: This package uses GitFlow, any development work should be done off the develop branches and
pull requests made against develop, not master.

```bash
git clone https://github.com/evansde77/cirrus.git
cd cirrus
git cirrus build
```

For more detailed docs see the [Installation Docs](https://github.com/evansde77/cirrus/wiki/Installation) 

User Configuration File:
========================

As cirrus works as a git extension, it will use your gitconfig file. The installer will create a cirrus section in this file and create the following settings:

1. *github-user* - Your Github Username
1. *github-token* - A github access token


Package Configuration Files:
============================

The per package controls used by cirrus live in a cirrus.conf file in the top level of the repo you use with cirrus.
This file, coupled with the cirrus setup.py template and command line tools dictate the behaviour of the cirrus commands within the package. Details for the cirrus config are in the (TBA) Configuration.MD file


Cirrus Commands:
================

See the [Cirrus Commands Docs](https://github.com/evansde77/cirrus/wiki#command-reference)

#### cirrus hello
A simple test command that says hello, verifies that things are working and prints out some info about your cirrus install

Usage:
```bash
git cirrus hello
```


* [git cirrus build](https://github.com/evansde77/cirrus/wiki/BuildCommand)
* [git cirrus test](https://github.com/evansde77/cirrus/wiki/TestCommand)
* [git cirrus release](https://github.com/evansde77/cirrus/wiki/ReleaseCommand)
* [git cirrus feature](https://github.com/evansde77/cirrus/wiki/FeatureCommand)
* [git cirrus docker-image](https://github.com/evansde77/cirrus/wiki/DockerImageCommand)
* [git cirrus selfupdate](https://github.com/evansde77/cirrus/wiki/SelfupdateCommand)




#### cirrus review
The cirrus review command provides some utilities for dealing with GitHub pull requests from the cirrus command line.
Available commands are:

 * git cirrus review list - list all open PRs for the repo, accepts -u or --user to filter for requests from a specific user
 * git cirrus review details - Get details for a specific PR, specified by --id
 * git cirrus review plusone - Set a Github context for the PR to indicate that the PR has been approved
 * git cirrus review review - Add a review comment to a PR, optionally adding the plusone flag to it as well


Examples:

```bash
git cirrus review list --user evansde77 # list open PRs by user evansde77
git cirrus review list                  # list all open PRs
git cirrus review plusone --id 500 -c "+1"      # adds the +1 context to the feature via a status update and sets it to success
git cirrus review reviee --id 500 -m "great work, LGTM"  --plus-one -c "+1" # adds a comment to the PR and sets the +1 context status to success
```






#### cirrus qc
Command for running quality control checks via pylint, pyflakes, pep8.

Usage:
```bash
git cirrus qc --files --only-changes --pylint --pyflakes --pep8
```

Options and config:
Running with no arguments will run all checks on everything. To run only a specific checker (pylint, pyflakes, or pep8) use the corosponding argument or a combonation of them.
Specific files may be ran using '--files' OR check only files that have not yet been commited to the repo by using the '--only-changes' argument.
For pylint, a score threshold must be set in cirrus.conf [quality] threshold. The path to an optional rcfile (pylint configuration) may be set at [quality] rcfile.



#### cirrus docs
Command for publishing Sphinx documentation

Usage:

```bash
git cirrus docs build
git cirrus docs pack
git cirrus docs publish
```

Options and config:

1. `git cirrus docs build`: `--make <options>`
    1. When run without `--make`, the default options `clean html` are used
    2. Requires a `sphinx_makefile_dir` value set in the `doc` section of cirrus.conf.
    3. `sphinx_makefile_dir` should point to the directory that contains Sphinx's Makefile.
2. `git cirrus docs pack` requires the following options in cirrus.conf [doc] section:
    * sphinx_doc_dir - should point to the directory where the documentation to be packaged is.
        E.g. /docs/\_build/html
    * artifact_dir - should point to the directory where the documentation artifact should be saved.
3. `git cirrus docs publish` requires the following options in cirrus.conf [doc] section:
    * publisher - the publisher plugin to use
    1. The publisher selected should have a section in cirrus.conf which contains the publisher options. Available publisher plugins can be found in /cirrus/plugins/publishers
        1. If using the `doc_file_server` plugin:
            1. in cirrus.conf:
                * doc_file_server_url - the URL of the server the documentation is uploaded to
                * doc_file_server_upload_path - the path to the location on the server the documentation should be uploaded to
                * doc_file_server_sudo - a value of True or False for if sudo should be used when issuing the Fabric `put` command
                    _Note:_ Optional if doc_file_server_sudo is False
            2. in the [cirrus] section of your .gitconfig:
                * file-server-username - the username used for the documentation file server
                * file-server-keyfile - the path the ssh keyfile to use when uploading the documentation
        2. If using the `jenkins` plugin:
            1. in cirrus.conf:
                * url - the URL of the Jenkins server
                * doc_job - the name of the Jenkins job for the documentation build
                * doc_var - the variable name which the uploaded documentation tarball will be accessed by (Jenkins File Parameter)
                * arc_var - the variable that will be used to name the file/folder the archive should be unpacked to as determined by the name of the archive filename. I.e. package-0.0.0.tar.gz => package-0.0.0 (Jenkins String Parameter)
                * extra_vars - boolean value indicating if there are move variables to send to Jenkins which should be defined in the section [jenkins_docs_extra_vars]
            2. in the [cirrus] section of your .gitconfig:
                * buildserver-user - Jenkins username for authorization
                * buildserver-token - token or password for authorization

Example cirrus.conf:

```ini
[doc]
sphinx_makefile_dir = docs/
sphinx_doc_dir = docs/_build/html
artifact_dir = docs/artifacts
publisher = doc_file_server

[doc_file_server]
doc_file_server_url = http://localhost:8080
doc_file_server_upload_path = /docs/package/archive
doc_file_server_sudo = True
```

If using `publisher = jenkins`:

```ini
[jenkins]
url = https://localhost:8080
doc_job = doc_build
doc_var = artifact
arc_var = ARCHIVE
extra_vars = True

[jenkins_docs_extra_vars]
var = value
var1 = value1
```
