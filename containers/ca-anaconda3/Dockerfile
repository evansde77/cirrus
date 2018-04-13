FROM continuumio/anaconda3:latest
MAINTAINER dave.evans@imc.com

ENV USER=some_user
ADD install_python.sh /opt/install_python.sh
ADD entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/install_python.sh /opt/entrypoint.sh
RUN /opt/install_python.sh


COPY cirrus-cli-latest.tar.gz /opt/
ADD scratch_test.sh /opt/scratch_test.sh
ADD clone_test.sh /opt/clone_test.sh
RUN chmod +x /opt/scratch_test.sh /opt/clone_test.sh
ENTRYPOINT ["/opt/scratch_test.sh"]



