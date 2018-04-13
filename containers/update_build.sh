#!/bin/bash

export REPO_DIR=`git rev-parse --show-toplevel`
cd $REPO_DIR
python setup.py sdist
latest=`ls -tr ${REPO_DIR}/dist/*.tar.gz | tail -1`
cp $latest ${REPO_DIR}/containers/py2.7/cirrus-cli-latest.tar.gz
cp $latest ${REPO_DIR}/containers/py3.5/cirrus-cli-latest.tar.gz
cp $latest ${REPO_DIR}/containers/py3.6/cirrus-cli-latest.tar.gz
cp $latest ${REPO_DIR}/containers/anaconda3-4.4.0/cirrus-cli-latest.tar.gz
cp $latest ${REPO_DIR}/containers/anaconda3-5.1.0/cirrus-cli-latest.tar.gz
cp $latest ${REPO_DIR}/containers/ca-anaconda3/cirrus-cli-latest.tar.gz
cd - 
