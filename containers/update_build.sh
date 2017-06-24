#!/bin/bash


python setup.py sdist

latest=`ls -tr dist/*.tar.gz | tail -1`
cp $latest containers/py2.7/cirrus-cli-latest.tar.gz
cp $latest containers/py3.5/cirrus-cli-latest.tar.gz
cp $latest containers/py3.6/cirrus-cli-latest.tar.gz

