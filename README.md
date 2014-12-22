sos-ci - Simple OpenStack Continuous Integration
================================================

This is a somewhat simple app to let you implement a third-pary CI
setup for OpenStack in your own lab.  It's a fork of an idea introduced
by Duncan Thomas here: https://github.com/Funcan/kiss-ci

Requirements
------------
Current requirements and assumptions.

- You have to have an OpenStack Third Party CI account to monitor the Gerrit Stream
- All of this work thus far assumes running on an OpenStack Cloud
- Update/Modify sos_ci/ansible/vars.yml for your OpenStack creds
- If you want to do multi-nic (ie: seperate network for iSCSI, use multi-nic options)


Current Status
--------------
Update Dec 22, 2014
* Been running this for a few months now, pretty reliably
* Only issues I've encountered are cleanup issues from Tempest
  after busy weeks I can get to a point where I have over 5K accounts
  and several thousan volumes, rather than messing with trying to detect
  the state in ansible and cleanup during idle period, I just wrote a
  cron job to do this for me each day.

Still very much a work in progress.  Where it stands as of Aug 25, 17:50 UTC
* Source your OpenStack creds file
* Make sure default image-id, flavor, key-name etc are good, or specify in a creds file (to be added)
* Launch with two listener threads
* Picks events off of gerrit listener, and puts them in a queue
* Currently queue processor just launches an instance, sleeps 60 seconds and deletes instance
* Grabs next event in queue

TODO
-----
Now that it works reliably, at some point I'll factor out the Ansible
pieces into their own repo and make it a sub-repo of sos-ci.

Also there's a ton of low hanging fruit here in terms of optimizations and
cleanup, but the whole point of this effort was to setup a CI automation system
with little overhead and a fire and forget type of reliability... that's done so
I may or may not come back to it.

Highlights
----------
Some highlighted points, and maybe answers to some questions.

- Should work in any environment with just the addition of your own custom RC files
- Pretty much just raw Python code just like kiss
- Unlike kiss however we add a threaded job processor (my answer to node-pool, kinda)
- Allow pluggable pieces for instance deployment and devstack/tempest run
  Idea here is if you use Vagrant for deployment... cool, if you use Salt... cool
  Use what you like and what you have, but you can always just use good old simple
  python with ssh.

Stats
-----
stack-time             : 20:41
stack-time with squid  :
stack-time with preseed:

Questions
---------

