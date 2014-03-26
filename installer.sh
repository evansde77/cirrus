#!/bin/bash

#
# installer for cirrus
# Sets up working dir eg $HOME/.cirrus
# Clones latest stable tag of cirrus into it
# runs setup commands to build venv for cirrus
# installs git alias commands
# gets token for github access & updates .gitconfig

INSTALL_DIR="${HOME}/.cirrus"
DEFAULT_USER="${USER}"
CIRRUS_REPO="git@github.com:evansde77/cirrus.git"

read -p "Installation directory [${INSTALL_DIR}]: " LOCATION
LOCATION=${LOCATION:-$INSTALL_DIR}

echo "Installing cirrus in ${LOCATION}..."
mkdir -p $LOCATION

echo "Installing cirrus to LOCATION=${LOCATION}" > ${LOCATION}/install.log
cd $LOCATION
# replace this with git clone of cirrus repo
git clone ${CIRRUS_REPO} cirrus 1 >> ${LOCATION}/install.log

cd cirrus
# bootstrap virtualenv
virtualenv --distribute venv
. venv/bin/activate
pip install -r requirements.txt 1>> ${LOCATION}/install.log

# run installer
export CIRRUS_HOME=$LOCATION/cirrus
export VIRTUALENV_HOME=$LOCATION/cirrus/venv
python bootstrap.py
python setup.py develop  1>> ${LOCATION}/install.log


