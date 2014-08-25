#!/bin/bash

REF_DATA=$1
mkdir ~/$REF_DATA
mkdir ~/$REF_DATA/logs
mkdir ~/$REF_DATA/logs/etc
mkdir ~/$REF_DATA/logs/etc/cinder

# devstack logs
cd ~/devstack
gzip -c local.conf > ~/upload_results/logs/local.conf.txt.gz

# cinder.conf
cd /etc/cinder
gzip -c cinder.conf > ~/upload_results/logs/etc/cinder/cinder.conf.txt.gz
gzip -c api-paste.ini > ~/upload_results/logs/etc/cinder/api-paste.ini.txt.gz
gzip -c policy.json > ~/upload_results/logs/etc/cinder/policy.json.txt.gz

# OS Service Logs
cd /opt/stack/screen-logs
for log in `ls -1 /opt/stack/screen-logs | grep "[a-zA-Z].log"`; do
    gzip -c $log > ~/upload_results/logs/$log.txt.gz
done

# Tempest logs
cd /opt/stack/tempest
gzip -c console.log.out > ~/upload_results/console.log.out
scp -r ~/$REF_DATA sfci:~/www/solidfire-ci-logs/
