#!/bin/bash
#
# installer for cirrus by an automated process
# Sets up working dir eg $HOME/.cirrus
# Pip installs the latest version of cirrus unless CIRRUS_VERSION_OVERRIDE
# is used to specify a version.
# creates a new virtualenv
# runs cirrus selfsetup commands to build venv for cirrus
# installs git alias commands
# Adds credentials to gitconfig or keyring
# You can override settings passed to the setup script via environment
# - CIRRUS_PYPI_USERNAME
# - CIRRUS_PYPI_TOKEN
# - CIRRUS_GITHUB_USERNAME
# - CIRRUS_GITHUB_TOKEN
# - CIRRUS_SSH_USERNAME
# - CIRRUS_SSH_KEYFILE
#
# The pip install defaults to the main pypi server for install,
# this can be overridden using CUSTOM_PYPI_SERVER to provide a URL
# to be passed to pip install --index-url

# prerequisites are pip and virtualenv
pip --version
if [ $? -eq 127 ]; then
    echo "pip binary not found, cannot proceed"
    exit 127
fi

virtualenv --version
if [ $? -eq 127 ]; then
    echo "virtualenv binary not found, cannot proceed"
    exit 127
fi


function latest_cirrus(){
    # Function that checks the github latest URL redirect to get
    # the latest version number
    local URL
    URL=`curl -s  -I https://github.com/evansde77/cirrus/releases/latest | grep '^Location:' | cut -d' ' -f2`
    URL=$(echo $URL|tr -d '\r')
    VERSION=`echo $URL | awk -F'/' '{print $NF}'`
    echo "$VERSION"
}

if [ -z "$CIRRUS_INSTALL" ]; then
    INSTALL_DIR="${HOME}/.cirrus"
else
    INSTALL_DIR=$CIRRUS_INSTALL
    echo "CIRRUS_INSTALL is set to: ${CIRRUS_INSTALL}"
fi

CIRRUS_VERSION=$(latest_cirrus)

if [ ! -z "$CIRRUS_VERSION_OVERRIDE" ]; then
    echo "CIRRUS_VERSION is set to: {$CIRRUS_VERSION_OVERRIDE}"
    CIRRUS_VERSION="${CIRRUS_VERSION_OVERRIDE}"
fi

CUSTOM_PYPI_SERVER=${CIRRUS_PYPI_URL:-""}

echo "Installing to: $INSTALL_DIR"
DEFAULT_USER="${USER}"
LOCATION=${2:-$INSTALL_DIR}


if [ -f $LOCATION ]; then
    rm -rf $LOCATION
fi

echo "Installing cirrus in ${LOCATION}..."
mkdir -p $LOCATION

echo "Installing cirrus to LOCATION=${LOCATION}" > ${LOCATION}/install.log
cd $LOCATION

if [ -f "./cirrus" ]; then
    rm -rf ./cirrus
fi

# bootstrap virtualenv
virtualenv  venv
. venv/bin/activate
if [ "x$CUSTOM_PYPI_SERVER" == "x" ];then
    pip install cirrus-cli==${CIRRUS_VERSION} 1>> ${LOCATION}/install.log    
else
    pip install --index-url=${CUSTOM_PYPI_SERVER} cirrus-cli==${CIRRUS_VERSION} 1>> ${LOCATION}/install.log
fi

# Environment overrides for settings:
PYPI_USERNAME=${CIRRUS_PYPI_USERNAME:-""}
PYPI_TOKEN=${CIRRUS_PYPI_TOKEN:-""}
GH_USERNAME=${CIRRUS_GITHUB_USERNAME:-""}
GH_TOKEN=${CIRRUS_GITHUB_TOKEN:-""}
SSH_USERNAME=${CIRRUS_SSH_USERNAME:-""}
SSH_KEYFILE=${CIRRUS_SSH_KEYFILE:-""}

CLI_OPTS=""

function append_cli_opt(){
    if [ "x${2}" != "x" ]; then
        CLI_OPTS+=" --${1}=${2}"
    fi
}

append_cli_opt "pypi-username" "${PYPI_USERNAME}"
append_cli_opt "pypi-token" "${PYPI_TOKEN}"
append_cli_opt "github-username" "${GITHUB_USERNAME}"
append_cli_opt "github-token" "${GITHUB_TOKEN}"
append_cli_opt "ssh-username" "${SSH_USERNAME}"
append_cli_opt "ssh-keyfile" "${SSH_KEYFILE}"

# run installer
export CIRRUS_HOME=$LOCATION
export VIRTUALENV_HOME=$LOCATION/venv
selfsetup --robot ${CLI_OPTS}



