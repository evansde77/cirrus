#!/bin/bash

export PYENV_ROOT=/opt/pyenvy
mkdir -p /opt/pyenvy

git clone https://github.com/yyuu/pyenv.git ${PYENV_ROOT}
export PATH=${PYENV_ROOT}/bin:${PATH}
eval "$(pyenv init -)"

pyenv install 2.7.11
pyenv global 2.7.11
curl -L https://bootstrap.pypa.io/get-pip.py | bash
pip install --upgrade pip setuptools virtualenv
virtualenv -p python2.7 /opt/venv




