#!/bin/bash

export REPO_DIR=`git rev-parse --show-toplevel`
export CONTAINERS_DIR=${REPO_DIR}/containers


function run_test(){
    echo "Running ${1}..."
    cd ${1}
    docker build -t cirrus-${1}:latest .
    docker run -ti --entrypoint /opt/scratch_test.sh cirrus-${1}:latest
    docker run -ti --entrypoint /opt/clone_test.sh cirrus-${1}:latest
    cd $CONTAINERS_DIR
}



declare -a VERSIONS=("ca-anaconda3" "anaconda3-5.1.0" "anaconda3-4.4.0" "py2.7" "py3.5" "py3.6")

for i in "${VERSIONS[@]}"
do
   run_test $i
done
