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


Current Status
--------------
Still very much a work in progress.  Where it stands as of Aug 25, 17:50 UTC
* Source your OpenStack creds file
* Make sure default image-id, flavor, key-name etc are good, or specify in a creds file (to be added)
* Launch with two listener threads
* Picks events off of gerrit listener, and puts them in a queue
* Currently queue processor just launches an instance, sleeps 60 seconds and deletes instance
* Grabs next event in queue

TODO
-----
Add the actual Tempest job and log upload bits

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

