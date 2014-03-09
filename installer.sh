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
CIRRUS_REPO="file:///Users/david/Documents/work/repos/cirrus"

read -p "Installation directory [${INSTALL_DIR}]: " LOCATION
LOCATION=${LOCATION:-$INSTALL_DIR}
echo "Installing cirrus to LOCATION=${LOCATION}" > $INSTALL_DIR/install.log

echo "Installing cirrus in ${LOCATION}..."
mkdir -p $LOCATION
cd $LOCATION
# replace this with git clone of cirrus repo
git clone ${CIRRUS_REPO} -b develop cirrus >> $INSTALL_DIR/install.log

cd cirrus
# bootstrap virtualenv
virtualenv --distribute venv
. venv/bin/activate
pip install -r bootstrap-requirements.txt 1>> $INSTALL_DIR/install.log

# run installer
export CIRRUS_HOME=$LOCATION/cirrus
export VIRTUALENV_HOME=$LOCATION/cirrus/cirrus/venv
python bootstrap.py
python setup.py develop  1>> $INSTALL_DIR/install.log


