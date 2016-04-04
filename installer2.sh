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

# bootstrap virtualenv
virtualenv venv
. venv/bin/activate
pip install cirrus-cli 1>> ${LOCATION}/install.log

export CIRRUS_HOME=$LOCATION
export VIRTUALENV_HOME=$LOCATION/venv
selfsetup





