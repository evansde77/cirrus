#!/bin/bash

export PYENV_ROOT=/opt/pyenvy
mkdir -p /opt/pyenvy

git clone https://github.com/yyuu/pyenv.git ${PYENV_ROOT}
git clone https://github.com/pyenv/pyenv-virtualenv.git ${PYENV_ROOT}/plugins/pyenv-virtualenv
export PATH=${PYENV_ROOT}/bin:${PATH}
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"


pyenv install anaconda3-5.1.0
pyenv global anaconda3-5.1.0
curl -O https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install --upgrade pip
pip install setuptools virtualenv









