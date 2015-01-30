#!/usr/bin/python

import sys

import executor


#patchset = 'refs/changes/26/111226/3'
#patchset = 'tempest'
#patchset = 'master'
patchset = str(sys.argv[1])
print "Testing patchset: %s" % patchset
success, results = executor.just_doit(patchset)
print "We'll ned to parse these out....\n%s" % results
