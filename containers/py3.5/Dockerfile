FROM centos:latest
MAINTAINER dave.evans@imc.com

RUN yum group install -y "Development Tools" && yum clean all && rm -rf /var/cache/yum/*
RUN yum install -y zlib-devel \
    bzip2-devel \
    openssl-devel \
    ncurses-devel \
    sqlite-devel \
    readline-devel \
    cyrus-sasl-devel \
    tk-devel \
    gdbm-devel \
    db4-devel \
    libpcap-devel \
    xz-devel && yum clean all && rm -rf /var/cache/yum/*

ENV PYENV_ROOT=/opt/pyenvy
ENV USER=some_user
ADD install_python.sh /opt/install_python.sh
RUN chmod +x /opt/install_python.sh
RUN /opt/install_python.sh


COPY cirrus-cli-latest.tar.gz /opt/
ADD scratch_test.sh /opt/scratch_test.sh
ADD clone_test.sh /opt/clone_test.sh
RUN chmod +x /opt/scratch_test.sh /opt/clone_test.sh
ENTRYPOINT ["/opt/clone_test.sh"]


