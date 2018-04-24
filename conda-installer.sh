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
DEFAULT_INSTALL_OPTS=""

read -p "Installation directory [${INSTALL_DIR}]: " LOCATION
LOCATION=${LOCATION:-$INSTALL_DIR}

echo "Installing cirrus in ${LOCATION}..."
mkdir -p $LOCATION

echo "Installing cirrus to LOCATION=${LOCATION}" > ${LOCATION}/install.log
cd $LOCATION

CIRRUS_INSTALLER_OPTIONS=${INSTALLER_OPTIONS:-$DEFAULT_INSTALL_OPTS}

CUSTOM_PYPI_SERVER=${CIRRUS_PYPI_URL:-""}
CIRRUS_VERSION=${CIRRUS_VERSION_OVERRIDE:-""}

CIRRUS_PIP_REQ="cirrus-cli"
if [ "x$CIRRUS_PIP_REQ" != "x" ];then
	CIRRUS_PIP_REQ+="$CIRRUS_VERSION"
fi

# bootstrap conda virtualenv
conda create -y -m -p ${LOCATION}/venv pip virtualenv
if [ -f "${LOCATION}/venv/bin/activate" ]; then
    source ${LOCATION}/venv/bin/activate ${LOCATION}/venv
else
   conda_loc=`which conda`
   conda_bin=`dirname $conda_loc`
   conda_base=`dirname $conda_bin`
   source ${conda_base}/etc/profile.d/conda.sh
   conda activate ${LOCATION}/venv
fi

if [ "x$CUSTOM_PYPI_SERVER" == "x" ];then
    pip install ${CIRRUS_PIP_REQ} 1>> ${LOCATION}/install.log
else
	pip install --index-url=${CUSTOM_PYPI_SERVER} ${CIRRUS_PIP_REQ} 1>> ${LOCATION}/install.log
fi


export CIRRUS_HOME=$LOCATION
export VIRTUALENV_HOME=$LOCATION/venv
selfsetup $CIRRUS_INSTALLER_OPTIONS





