#!/bin/bash

#
# clone_test
#
git config --global user.name "some_user"
git config --global user.email "some_email"

export PATH=${PYENV_ROOT}/bin:${PATH}
eval "$(pyenv init -)"

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

cp -rf  conda-cirrus.conf cirrus.conf

echo "****************Test CondaEnv Builder**************"
git cirrus build --clean --builder=CondaEnv --environment=conda-environment.yml --upgrade
echo "****************Test CondaPip Builder**************"
git cirrus build --clean --builder=CondaPip
echo "****************test Conda Builder*****************"
git cirrus build --clean --builder=Conda --extra-requirements=conda-test-requirements.txt


git cirrus test --test-options "-e py36" -b Conda

git add -A && git commit -m "cleanup unmerged files"
git cirrus feature new test_integ
git cirrus feature merge

git cirrus release new --micro --no-remote
git cirrus release build
git cirrus release merge --cleanup --no-remote









