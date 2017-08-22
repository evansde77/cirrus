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

# prerequisites are pip and virtualenv
pip --version 2>/dev/null
if [ $? -eq 127 ]; then
    echo "pip binary not found, cannot proceed"
    exit 127
fi

virtualenv --version 2>/dev/null
if [ $? -eq 127 ]; then
    echo "virtualenv binary not found, cannot proceed"
    exit 127
fi

read -p "Installation directory [${INSTALL_DIR}]: " LOCATION
LOCATION=${LOCATION:-$INSTALL_DIR}

echo "Installing cirrus in ${LOCATION}..."
mkdir -p $LOCATION

echo "Installing cirrus to LOCATION=${LOCATION}" > ${LOCATION}/install.log
cd $LOCATION

CUSTOM_PYPI_SERVER=${CIRRUS_PYPI_URL:-""}
CIRRUS_VERSION=${CIRRUS_VERSION_OVERRIDE:-""}

CIRRUS_PIP_REQ="cirrus-cli"
if [ "x$CIRRUS_PIP_REQ" != "x" ];then
	CIRRUS_PIP_REQ+="$CIRRUS_VERSION"
fi

# bootstrap virtualenv
virtualenv venv
. venv/bin/activate

if [ "x$CUSTOM_PYPI_SERVER" == "x" ];then
    pip install ${CIRRUS_PIP_REQ} 1>> ${LOCATION}/install.log    
else
	pip install --index-url=${CUSTOM_PYPI_SERVER} ${CIRRUS_PIP_REQ} 1>> ${LOCATION}/install.log
fi


export CIRRUS_HOME=$LOCATION
export VIRTUALENV_HOME=$LOCATION/venv
selfsetup





