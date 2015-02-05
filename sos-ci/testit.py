#!/usr/bin/python

import sys

import executor


#patchset = 'refs/changes/26/111226/3'
#patchset = 'tempest'
#patchset = 'master'
patchset = str(sys.argv[1])
print "Testing patchset: %s" % patchset
(hash_id, success, results) = executor.just_doit(patchset)
print "hash_id:%s", hash_id
print "success:%s", success
print "result:%s", results
