#!/bin/bash

export PYENV_ROOT=/opt/pyenvy
mkdir -p /opt/pyenvy

git clone https://github.com/yyuu/pyenv.git ${PYENV_ROOT}
export PATH=${PYENV_ROOT}/bin:${PATH}
eval "$(pyenv init -)"

pyenv install 2.7.12
pyenv global 2.7.12
curl -O https://bootstrap.pypa.io/get-pip.py
python2.7 get-pip.py
pip install --upgrade pip setuptools virtualenv
virtualenv -p python2.7 /opt/venv




