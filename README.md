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
2. pypi Section
  1. pypi_url - If present, will use the pypi server to install requirements, also requires the pypi username and token to be set in the cirrus section of your gitconfig
3. Other options
  1. `-c, --clean` removes the existing ./venv before building.
  2. `-d, --docs` generate documentation using Sphinx and its generated Makefile.  Any optional make commands can be passed along (e.g., --docs clean singlehtml)
    1.  Requires a `sphinx_makefile_dir` value set in the `docs` section of cirrus.conf.
    2. `sphinx_makefile_dir` should point to the directory that contains Sphinx's Makefile.


#### cirrus feature
Commands related to the creatation and management of a git-flow style feature branch.

1. new - Creates a new feature branch, optionally pushing the new branch upstream following a git-flow style workflow
2. pull-request - Creates a new Pull Request in github requesting to merge the current feature branch with the develop branch, specifying the title, body and list of people to tag in the PR.
3. pr - shorthand for pull-request
4. list - lists all open unmerged feature branches in the repo

Usage:
```bash
git cirrus feature new BRANCH_NAME --push
git cirrus feature pull-request --title TITLE --body BODY --notify @AGITHUBUSER,@ANOTHERGITHUBUSER
```

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

#### cirrus release
Commands related to creation of a new git-flow style release branch, building the release and uploading it to a pypi server.
There are three subcommands:

1. new - creates a new release branch, increments the package version, builds the release notes if configured.
2. build - Runs sdist to create a new build artifact from the release branch
3. merge - Runs git-flow style branch merges back to master and develop, optionally waiting on CI or setting flags for GH build contexts if needed
4. upload - Pushes the build artifact to the pypi server configured in the cirrus conf, using a plugin system to allow for customisation.

Usage:
```bash
git cirrus test # Stop if things are broken
git cirrus release new --micro
git cirrus release build
git cirrus release merge --cleanup
git cirrus release upload --plugin pypi
```

Options:

1. release new requires one of --micro, --minor or --macro to indicate which semantic version field to increment
2. --bump adds or updates a package==version pair in requirements.txt, e.g. `--bump foo==0.0.9 bar==1.2.3`.
3. release merge supports the following options:
  * --cleanup - removes the remote and local release branch on successful merge
  * --context-string - Update the github context string provided when pushed
  * --wait-on-ci - Wait for GitHub CI status to be success before uploading
4. upload will push the new release and upload the build artifact to pypi, but may take several non-required options:
  * --plugin - Name of the upload plugin module. Options are found in [https://github.com/evansde77/cirrus/tree/develop/src/cirrus/plugins/uploaders](cirrus/plugins/uploaders) and can be used to customise the upload process. The pypi plugin does a standard sdist upload to the pypi server configured in your pypirc. The fabric plugin uses fabric to scp the artifact to a custom pypi server.
  * --test do not push new release or upload build artifact to pypi
  * --pypi-sudo, --no-pypi-sudo use or do not use sudo to move the build artifact to the correct location in the pypi server, defaults to using sudo
  * --pypi-url URL override the pypi url from cirrus.conf with URL, equivalent to the -r option for pypi.python.org uploads, can specify a url or a shorthand name from your pypirc.


Release Options in cirrus.conf

You can customise the release merge workflow for each package via the cirrus config with the following settings:

 * wait_on_ci - Set true to enable waiting on CI builds for the release branch, defaults to False, this will make the merge command poll the GH status API for the commit and wait for it to become success
 * wait_on_ci_develop - Set true to enable waiting on CI builds for the develop branch, defaults to False
 * wait_on_ci_master - Set true to enable waiting on CI builds for the master branch, defaults to False
 * wait_on_ci_timeout - Timeout in seconds to give up on waiting on CI, defaults to 600s (10 mins)
 * wait_on_ci_interval - Interval to poll status in seconds, defaults to 2 seconds
 * github_context_string - The github context to update status for if update_github_context is True  Eg: continuous-integration/travis-ci
 * update_github_context - An alternative to waiting on CI, you can simply flip the status for a context to success if eg you have protected branches without a CI build to wait for. Requires a context to be provided via the github_context_string setting
 * push_retry_attempts - Optional number of attempts to try to push during merge
 * push_retry_cooloff - Optional time to wait between retries in seconds

Example:

```ini
[release]
wait_on_ci = False
wait_on_ci_develop = False
wait_on_ci_master = False
wait_on_ci_timeout = 600
wait_on_ci_interval = 2
github_context_string = continuous-integration/travis-ci
update_github_context = True
push_retry_attempts = 10
push_retry_cooloff = 2
```

##### Working with GitHub protected branches

The release command works with two possible mode of [https://github.com/blog/2051-protected-branches-and-required-status-checks](GitHub branch protection) one in which you wait for the CI tests to run and update the status, and one in which there are no checks, so that you have to set status to merge branches in a git flow style.

For the waiting mode, simply flip the boolean wait_on_ci flag to True to wait on CI to run on the release branch. Likewise, the wait_on_ci_develop and wait_on_ci_master params will wait on CI status for the develop and master branches you have configured before merging. You can adjust the total timeout in seconds and the poll interval via the cirrus config file.

For the non-waiting mode, you provide the github context string you want to set and then when the merges back to develop and master occur, that state value is set to success. This mode of operation is useful when your CI system runs release tests in a way not connected to github, but you still have protected branches.

##### release tips

*Protip:* If you don't make releases regularly, you'll want to make sure your local repo copy is up to date (cirrus should do these eventually).


```
git checkout master # get master, if you only have develop
git fetch
git fetch --tags
git checkout develop # you're ready to release!
```

*Protip:* If something goes wrong during release building you may end up on a release/A.B.C branch that didn't work out. If you haven't pushed out the tag for the new version you can `git checkout develop` and `git branch -d release/A.B.C`. If you've pushed a bad version/tag the best thing to do is resolve the problem and create a new micro version -- don't modify a tag that's already remote (consult your own release workflow).


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


#### cirrus deploy

The deploy command provides a plugin driven way to hook into deployment systems like chef and puppet.
Since deployment is heavily customisable based on what system is in use, the command supports selecting a plugin and then delegates all CLI options to that plugin.

Usage:
```bash
git cirrus deploy --plugin=<plugin_name>  <options for plugin>
```

Deployer plugins live in [cirrus.plugins.deployers](https://github.com/evansde77/cirrus/tree/develop/src/cirrus/plugins/deployers) and individual docs for each plugin can be found there.

Plugins:

 * [chef](https://github.com/evansde77/cirrus/blob/develop/src/cirrus/plugins/deployers/chef.py) - [docs](https://github.com/evansde77/cirrus/blob/develop/src/cirrus/plugins/deployers/chef.md)


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
