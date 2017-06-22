#!/bin/bash

#
# scratch_test
#
git config --global user.name "some_user"
git config --global user.email "some_email"



TIMESTAMP=`date +%s`
REPO_DIR="test_${TIMESTAMP}"
mkdir -p $REPO_DIR
cd $REPO_DIR
git init


# set up a new package
git cirrus package init --bootstrap -p imc.group.package -v 0.0.0 -s src --no-remote -o imc -d "this is a test"  --python python2.7
# set up simple container templates
git cirrus package container-init  --local-install --base-image python:2.7 --no-remote
git cirrus build   # build local dev virtualenv
# this is where you would add code and tests
git cirrus test                                     # run tests
git cirrus release build                  # create a build artifact to add to the container
git cirrus docker-image build    # build the container & install this package on it

