#!/bin/bash

#
# installer for cirrus
# Sets up working dir eg $HOME/.cirrus
# Clones latest stable tag of cirrus into it
# runs setup commands to build venv for cirrus
# installs git alias commands
# gets token for github access & updates .gitconfig


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



echo "Installing to: $INSTALL_DIR"
DEFAULT_USER="${USER}"
CIRRUS_TARFILE="${CIRRUS_VERSION}.tar.gz"
CIRRUS_UNPACK_DIR="cirrus-${CIRRUS_VERSION}"
CIRRUS_URL="https://github.com/evansde77/cirrus/archive/${CIRRUS_TARFILE}"


LOCATION=${2:-$INSTALL_DIR}


if [ -f $LOCATION ]; then
    rm -rf $LOCATION
fi

echo "Installing cirrus in ${LOCATION}..."
mkdir -p $LOCATION

echo "Installing cirrus to LOCATION=${LOCATION}" > ${LOCATION}/install.log
cd $LOCATION

if [ -f $CIRRUS_TARFILE ]; then
    rm -rf $CIRRUS_TARFILE
fi

curl -LO $CIRRUS_URL
tar -zxf $CIRRUS_TARFILE
if [ -f "./cirrus" ]; then
    rm -rf ./cirrus
fi
ln -s ./${CIRRUS_UNPACK_DIR} ./cirrus

ls -al .


cd cirrus
# bootstrap virtualenv
virtualenv  venv
. venv/bin/activate
pip install -r requirements.txt 1>> ${LOCATION}/install.log

# run installer
export CIRRUS_HOME=$LOCATION/cirrus
export VIRTUALENV_HOME=$LOCATION/cirrus/venv
python bootstrap.py -y
python setup.py develop  1>> ${LOCATION}/install.log


