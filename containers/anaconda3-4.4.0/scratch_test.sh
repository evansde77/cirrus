#!/bin/bash

#
# scratch_test
#
git config --global user.name "some_user"
git config --global user.email "some_email"

export PATH=${PYENV_ROOT}/bin:${PATH}
eval "$(pyenv init -)"


ACTIVATE_SCRIPT=${PYENV_ROOT}/versions/anaconda3-4.4.0/bin/activate
mkdir -p ~/.cirrus
conda create -y -m -p ~/.cirrus/venv pip


(

source ${ACTIVATE_SCRIPT} ~/.cirrus/venv
export LOCATION=~/.cirrus
pip install /opt/cirrus-cli-latest.tar.gz
export CIRRUS_HOME=${LOCATION}
selfsetup --robot
)

TIMESTAMP=`date +%s`
REPO_DIR="test_${TIMESTAMP}"
export USER=some_user
mkdir -p $REPO_DIR
cd $REPO_DIR
git init


# set up a new package
git cirrus package init --bootstrap -p test_package -v 0.0.0 -s src --no-remote -o integ_test -d "this is a test"  --python python3.6
git cirrus build   # build local dev virtualenv
# this is where you would add code and tests
git cirrus build --clean --upgrade --builder=CondaPip

git cirrus test                                     # run tests
git cirrus feature new integ_test --no-remote
git cirrus feature merge --no-remote
git cirrus release new --micro --no-remote
git cirrus release build                  # create a build artifact to add to the container
git cirrus release merge --cleanup --no-remote

