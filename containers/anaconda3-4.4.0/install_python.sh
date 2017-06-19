#!/bin/bash

export PYENV_ROOT=/opt/pyenvy
mkdir -p /opt/pyenvy

git clone https://github.com/yyuu/pyenv.git ${PYENV_ROOT}
export PATH=${PYENV_ROOT}/bin:${PATH}
eval "$(pyenv init -)"

pyenv install anaconda3-4.4.0
pyenv global anaconda3-4.4.0
curl -L https://bootstrap.pypa.io/get-pip.py | bash
pip install --upgrade pip setuptools virtualenv
conda create venv





