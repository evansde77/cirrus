#!/bin/bash

#
# clone_test
#
git config --global user.name "some_user"
git config --global user.email "some_email"

export PATH=${PYENV_ROOT}/bin:${PATH}
eval "$(pyenv init -)"

mkdir -p ~/.cirrus
virtualenv ~/.cirrus/venv
(

. ~/.cirrus/venv/bin/activate
export LOCATION=~/.cirrus
pip install /opt/cirrus-cli-latest.tar.gz
export CIRRUS_HOME=$LOCATION
export VIRTUALENV_HOME=$LOCATION/venv
selfsetup --robot

)

TIMESTAMP=`date +%s`
REPO_DIR="test_${TIMESTAMP}"
export USER=some_user
export ORIGIN_REPO=`pwd`/cirrus_test_origin
export TEST_REPO=`pwd`/cirrus_test

git clone https://github.com/evansde77/cirrus_test.git ${ORIGIN_REPO}
cd ${ORIGIN_REPO}
git fetch
git checkout -b master origin/master
git checkout -b develop origin/develop

git clone ${ORIGIN_REPO} ${TEST_REPO}
cd ${TEST_REPO}
git checkout -b master origin/master
git checkout -b develop origin/develop

git cirrus build
git cirrus test --test-options "-e py27"

git cirrus feature new test_integ
git cirrus feature merge

git cirrus release new --micro --no-remote
git cirrus release status
git cirrus release build                  # create a build artifact to add to the container
git cirrus release merge --cleanup --no-remote
git cirrus release status --release=release/0.0.5








