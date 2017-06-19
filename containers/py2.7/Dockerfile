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

ADD install_python.sh /opt/install_python.sh
ADD entrypoint.sh /opt/entrypoint.sh 
RUN chmod +x /opt/install_python.sh /opt/entrypoint.sh
RUN /opt/install_python.sh
ENTRYPOINT ["/opt/entrypoint.sh"]


