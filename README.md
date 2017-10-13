cirrus
======

python library build, test and devop like things assistant

[![Build Status](https://travis-ci.org/cloudant/cirrus.svg?branch=develop)](https://travis-ci.org/cloudant/cirrus)

Installation Prerequisites
==========================

* Cirrus requires either python/pip/virtualenv or conda and has been tested with python2.7, 3.5 and 3.6 as of Release 0.2.0.
   * Since python3 support and conda support are fairly new, please report any problems as Issues in this project.
* Git tools are heavily used, git is a requirement as cirrus is accessed via git command aliases.

Documentation
=============

Expanded Docs are available on the [Package Wiki](https://github.com/cloudant/cirrus/wiki)

Installation as a user:
=======================

```bash
curl -O https://raw.githubusercontent.com/cloudant/cirrus/develop/installer.sh
bash installer.sh
```

Or if you are using anaconda:

```bash
curl -O https://raw.githubusercontent.com/cloudant/cirrus/develop/conda-installer.sh
bash conda-installer.sh
```

See the

Installation for Development:
=============================

_Note_: This package uses GitFlow, any development work should be done off the develop branches and
pull requests made against develop, not master.

```bash
git clone https://github.com/cloudant/cirrus.git
cd cirrus
git cirrus build
```

For more detailed docs see the [Installation Docs](https://github.com/cloudant/cirrus/wiki/Installation)


Package Configuration Files:
============================

The per package controls used by cirrus live in a cirrus.conf file in the top level of the repo you use with cirrus.
This file, coupled with the cirrus setup.py template and command line tools dictate the behaviour of the cirrus commands within the package. Details for the cirrus config are in the [Cirrus Configuration Docs](https://github.com/cloudant/cirrus/wiki/CirrusConfiguration)


Cirrus Commands:
================

See the [Cirrus Commands Docs](https://github.com/cloudant/cirrus/wiki#command-reference)

* [git cirrus hello](https://github.com/cloudant/cirrus/wiki/HelloCommand) - Install check and version info
* [git cirrus build](https://github.com/cloudant/cirrus/wiki/BuildCommand) - Create a development environment
* [git cirrus test](https://github.com/cloudant/cirrus/wiki/TestCommand) - Run test suites
* [git cirrus release](https://github.com/cloudant/cirrus/wiki/ReleaseCommand) - Release code and push to pypi
* [git cirrus feature](https://github.com/cloudant/cirrus/wiki/FeatureCommand) - Work on new features
* [git cirrus docker-image](https://github.com/cloudant/cirrus/wiki/DockerImageCommand) - Build and release container images
* [git cirrus selfupdate](https://github.com/cloudant/cirrus/wiki/SelfupdateCommand) - Update cirrus
* [git cirrus qc](https://github.com/cloudant/cirrus/wiki/QCCommand) - Run quality control and code standard tests
* [git cirrus docs](https://github.com/cloudant/cirrus/wiki/DocsCommand) - Build sphinx package docs
* [git cirrus review](https://github.com/cloudant/cirrus/wiki/ReviewCommand) - Helper for GitHub Pull Requests





