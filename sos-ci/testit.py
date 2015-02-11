#!/usr/bin/python

import os
import sys

import executor


# patchset is of the form 'refs/changes/26/111226/3'
# results_dir is of the form '/home/user/test-dir'

patchset = str(sys.argv[1])
results_dir = str(sys.argv[2])

ref_name = patchset.replace('/', '-')

# build the dir
results_dir = results_dir + '/' + ref_name
os.mkdir(results_dir)

(hash_id, success, results) = executor.just_doit(patchset, results_dir)
print "hash_id:%s", hash_id
print "success:%s", success
print "result:%s", results
