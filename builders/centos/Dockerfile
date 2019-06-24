FROM centos:latest
MAINTAINER evansde@gmail.com

## Uncomment if you want to add your own yum.repo files
## ADD etc/yum.repos.d/*  /etc/yum.repos.d/

RUN yum update -y && yum group install -y "Development Tools" && yum clean all && rm -rf /var/cache/yum/*

RUN yum install -y zlib-devel \
                   bzip2-devel \
                   openssl-devel \
                   ncurses-devel \
                   sqlite-devel \
                   readline-devel \
                   cyrus-sasl-devel \
		   cyrus-sasl-gssapi \
                   libffi-devel \
                   tk-devel \
                   gdbm-devel   && yum clean all && rm -rf /var/cache/yum/*

RUN useradd -ms /bin/bash cirrus
USER cirrus
WORKDIR /home/cirrus
ADD bashrc /home/cirrus/.bashrc
COPY ssh /home/cirrus/.ssh

ENV PYENV_ROOT /home/cirrus/.pyenv
COPY pip /home/cirrus/.pip
COPY pypirc /home/cirrus/.pypirc
COPY gitconfig /home/cirrus/.gitconfig
COPY entrypoint /home/cirrus/entrypoint
RUN git clone https://github.com/pyenv/pyenv.git /home/cirrus/.pyenv

ARG PYTHON_VERSION=3.6.6
RUN . /home/cirrus/.bashrc && pyenv install ${PYTHON_VERSION} && pyenv global ${PYTHON_VERSION}
RUN . /home/cirrus/.bashrc && pip install -U pip setuptools virtualenv
RUN . /home/cirrus/.bashrc && virtualenv -p python /home/cirrus/.cirrus/venv
RUN . /home/cirrus/.bashrc && . /home/cirrus/.cirrus/venv/bin/activate && pip install cirrus-cli
ENV REPO_DIR="/repo"

ENTRYPOINT ["/home/cirrus/entrypoint"]



