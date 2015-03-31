sos-ci - Simple OpenStack Continuous Integration
================================================

This is a somewhat simple app to let you implement a third-pary CI
setup for OpenStack in your own lab.  It's a fork of an idea introduced
by Duncan Thomas here: https://github.com/Funcan/kiss-ci

The great thing is there's a number of folks using this now, and some
have even contributed back.  The BAD thing is that there are a number
of people that are running this now and apprantly know just next to
nothing about OpenStack.

Please, make sure you understand how tools like devstack and logging
in to OpenStack Instances works before trying this.  It would also
be VERY helpful to cruise on out to the your Internet Search Engine of
choice and read a bit about Ansible as well.

I recommend http://www.google.com for a lot of things.

Requirements
------------
Current requirements and assumptions.

- You have to have an OpenStack Third Party CI account to monitor the Gerrit Stream
- All of this work thus far assumes running on an OpenStack Cloud
- Update/Modify sos_ci/ansible/vars.yml for your OpenStack creds
- If you want to do multi-nic (ie: seperate network for iSCSI, use multi-nic options)
- In order to use the mail notification option, install:
  * postfix
  * sendmail
- Make sure you have the system you're running all of this on set up such that
  you can log on to your instances with SSH. Personally I set up my systems
  with a .ssh/config file that includes my OpenStack IP ranges and the key
  associated with them, but of course use whatever method you like.
- mysql db
  Added support for subunit2sql, so we can take subunit results and keep a local
  DB of what we've run.  You'll need to setup/configure a MySQL database and populate
  the schema prior to use.  This is great for collection stats like how many tests
  we've run, pass/fail rate, timings etc etc.  Eventually we'll use this to push up
  to a dashboard.

  Can be enabled/disabled via conf file.  For more info on subunit2sql check here for
  instructions and more info:
    http://docs.openstack.org/developer/subunit2sql/


Current Status
--------------

Update Mar 12, 2025
* Cleaned up the ansible config pieces a good bit
* Improved the logging
* Added hooks to create a DB and keep track of results/stats
* Remove hard coded variables that refer to my system and account

Update Dec 22, 2014
* Been running this for a few months now, pretty reliably
* Only issues I've encountered are cleanup issues from Tempest
  after busy weeks I can get to a point where I have over 5K accounts
  and several thousand volumes, rather than messing with trying to detect
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

Questions
---------

Q: SSH checks to Instances fail, how come?
A: Ansible uses SSH to connect to hosts, you need to make sure you have your system
   setup to use ssh keys appropriately. For me I use my .ssh/config file for this,
   you may have other methods you prefer, but for me I just have a config entry
   that specifies my keypair for any IP in the range of OpenStack cloud.


