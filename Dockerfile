# John Griffith '2015'

FROM ubuntu:14.04
MAINTAINER John Griffith "john.griffith8@gmail.com"

EXPOSE 80 3306
RUN apt-get -y update
RUN apt-get install -y git vim python-software-properties python-pip ruby lvm2 python-dev
RUN apt-get install -y python-novaclient
RUN apt-get install -y mysql-server libmysqlclient-dev
RUN apt-get install -y postfix

RUN git clone https://github.com/j-griffith/sos-ci
RUN pip install -r sos-ci/requirements.txt
RUN mkdir /etc/ansible
RUN copy -R sos-ci/etc.ansible/* /etc/ansible
