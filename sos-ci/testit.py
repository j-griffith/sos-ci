#!/usr/bin/python

import executor


#patchset = 'refs/changes/26/111226/3'
#patchset = 'tempest'
patchset = 'master'
results = executor.just_doit(patchset)
print "We'll ned to parse these out....\n%s" % results
