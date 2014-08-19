cirrus
======

python library build, test and devop like things assistant


Installation as a user:
=======================
Note: Prior to doing this step, you will need to have added your public key to GitHub so that you can clone the cirrus repo. See [this howto](https://help.github.com/articles/generating-ssh-keys) for details.


```bash
curl -O https://raw.githubusercontent.com/evansde77/cirrus/develop/installer.sh
bash installer.sh
```

The installer script will set up an install of cirrus for you in your home directory 
and prompt for some info so that it can set up some parameters in your .gitconfig 



Installation for Development:
=============================

_Note_: This package uses GitFlow, any development work should be done off the develop branches and 
pull requests made against develop, not master. 

```bash
git clone https://github.com/evansde77/cirrus.git 
git cirrus build
```


User Configuration File:
========================

As cirrus works as a git extension, it will use your gitconfig file. The installer will create a cirrus section in this file and create the following settings:

1. *github-user* - Your Github Username
1. *github-token* - A github access token
1. *pypi-user* - Username of your pypi server
1. *pypi-token* - Token/password to access your pypi server
1. *pypi-ssh-key* - SSH key used for scp-like uploads to your pypi server (if HTTP upload isnt supported)


Package Configuration Files:
============================

The per package controls used by cirrus live in a cirrus.conf file in the top level of the repo you use with cirrus. 
This file, coupled with the cirrus setup.py template and command line tools dictate the behaviour of the cirrus commands within the package. Details for the cirrus config are in the (TBA) Configuration.MD file


Cirrus Commands:
================ 

#### cirrus hello 
A simple test command that says hello, verifies that things are working and prints out some info about your cirrus install

Usage:
```bash
git cirrus hello
```


#### cirrus build
Builds a new virtualenv and installs the requirements for the package, setting up a development/testing/deployment environment for the package. 

Usage:
```bash
git cirrus build 
```

The virtualenv is created in ./venv. 
Optional parameters for the build command are read from the cirrus.conf, they are;

1. build Section
  1. virtualenv_name - sets the name of the virtualenv directory, defaults to venv
  2. requirements_file - name of the requirements.txt file, defaults to requirements.txt 
3. pypi Section
  4. pypi_url - If present, will use the pypi server to install requirements, also requires the pypi username and token to be set in the cirrus section of your gitconfig  


#### cirrus feature
Commands related to the creatation and management of a git-flow style feature branch.

1. new - Creates a new feature branch, optionally pushing the new branch upstream following a git-flow style workflow
2. pull-request - Creates a new Pull Request in github requesting to merge the current feature branch with the develop branch, specifying the title, body and list of people to tag in the PR. 

Usage:
```bash 
git cirrus feature new BRANCH_NAME --push
git cirrus feature pull-request --title TITLE --body BODY --notify @AGITHUBUSER,@ANOTHERGITHUBUSER
```


#### cirrus release
Commands related to creation of a new git-flow style release branch, building the release and uploading it to a pypi server. 
There are three subcommands:

1. new - creates a new release branch, increments the package version, builds the release notes if configured. 
2. build - Runs sdist to create a new build artifact from the release branch 
3. upload - Pushes the build artifact to the pypi server configured in the cirrus conf. 

Usage:
```bash 
git cirrus release new --micro 
# test things here!!
git cirrus release build 
git cirrus release upload 
```

Options:

1. release new requires one of --micro, --minor or --macro to indicate which semantic version field to increment


#### cirrus test
Command for running tests in a package.

Usage:
```bash 
git cirrus test
```

Options and config:
--suite SUITE_LOCATION

Must define name of virtualenv in [package] virtualenv
Must define [test-default] where (default location for tests, optional if you choose to always include --suite)
May define [test-SUITE_LOCATION] where
