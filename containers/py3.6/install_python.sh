#!/bin/bash

export PYENV_ROOT=/opt/pyenvy
mkdir -p /opt/pyenvy

git clone https://github.com/yyuu/pyenv.git ${PYENV_ROOT}
export PATH=${PYENV_ROOT}/bin:${PATH}
eval "$(pyenv init -)"

pyenv install 3.6.1
pyenv global 3.6.1
curl -O https://bootstrap.pypa.io/get-pip.py
python3.6 get-pip.py
pip install --upgrade pip setuptools virtualenv
virtualenv -p python3.6 /opt/venv




