#!/bin/bash

mkdir -p /opt/stack/logs
local u=""
local name=""
for u in `sudo systemctl list-unit-files | grep devstack | awk '{print $1}'`;
do
        name=$(echo $u | sed 's/devstack@/screen-/' | sed 's/\.service//')
            sudo journalctl -o short-precise --unit $u | sudo tee
            /tmp/logs/$name.txt > /dev/null
        done
