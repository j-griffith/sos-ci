#!/bin/bash

REF_NAME=$1
cd  /home/ubuntu/

mkdir $REF_NAME
mkdir $REF_NAME/logs
mkdir $REF_NAME/logs/etc

PROJECTS="openstack-dev/devstack $PROJECTS"
PROJECTS="openstack/cinder $PROJECTS"
PROJECTS="openstack/glance $PROJECTS"
PROJECTS="openstack/glance_store $PROJECTS"
PROJECTS="openstack/horizon $PROJECTS"
PROJECTS="openstack/keystone $PROJECTS"
PROJECTS="openstack/keystonemiddleware $PROJECTS"
PROJECTS="openstack/nova $PROJECTS"
PROJECTS="openstack/oslo.config $PROJECTS"
PROJECTS="openstack/oslo.db $PROJECTS"
PROJECTS="openstack/oslo.i18n $PROJECTS"
PROJECTS="openstack/oslo.messaging $PROJECTS"
PROJECTS="openstack/oslo.middleware $PROJECTS"
PROJECTS="openstack/oslo.rootwrap $PROJECTS"
PROJECTS="openstack/oslo.serialization $PROJECTS"
PROJECTS="openstack/oslo.vmware $PROJECTS"
PROJECTS="openstack/python-cinderclient $PROJECTS"
PROJECTS="openstack/python-glanceclient $PROJECTS"
PROJECTS="openstack/python-keystoneclient $PROJECTS"
PROJECTS="openstack/python-novaclient $PROJECTS"
PROJECTS="openstack/python-openstackclient $PROJECTS"
PROJECTS="openstack/requirements $PROJECTS"
PROJECTS="openstack/stevedore $PROJECTS"
PROJECTS="openstack/taskflow $PROJECTS"
PROJECTS="openstack/tempest $PROJECTS"

# devstack logs
cd /home/ubuntu/devstack
cp /home/ubuntu/devstack/local.conf /home/ubuntu/$REF_NAME/logs/local.conf.txt
cp /tmp/stack.sh.log.out /home/ubuntu/$REF_NAME/logs/stack.sh.log.out.txt

# Archive config files
for PROJECT in $PROJECTS; do
    proj=`basename $PROJECT`
    if [ -d /etc/$proj ]; then
        sudo cp -r /etc/$proj /home/ubuntu/$REF_NAME/logs/etc/
    fi
done

# OS Service Logs

# make it work with the new systemd settings
local u=""
local name=""
for u in `sudo systemctl list-unit-files | grep devstack | awk '{print $1}'`; do
    name=$(echo $u | sed 's/devstack@//' | sed 's/\.service//')
    sudo journalctl -o short-precise --unit $u | sudo tee /home/ubuntu/$REF_NAME/logs/$name.txt > /dev/null
done

# Add the commit id
cd /opt/stack/cinder
COMMIT = git log --abbrev-commit --pretty=oneline -n1
COMMIT_ID = var1=$(echo $COMMIT | cut -f1 -d-)
echo "commit_id: $COMMIT_ID" >> console.log.out

# Tempest logs
cd /opt/stack/tempest
cp console.log.out  /home/ubuntu/$REF_NAME/console.log.out
cp etc/tempest.conf  /home/ubuntu/$REF_NAME/logs/tempest.conf
cp results.html /home/ubuntu/$REF_NAME/testr_results.html
# Tar it all up
#cd $REF_NAME
cd /home/ubuntu/$REF_NAME
tar -cvf $REF_NAME.tar ./*
gzip $REF_NAME.tar
