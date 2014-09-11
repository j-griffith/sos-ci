#!/usr/bin/python

from collections import deque
import json
from optparse import OptionParser
import os
import paramiko
import sys
from threading import Thread
import time

import executor


# CI related variables
CI_ACCOUNT = os.environ.get('CI_ACCOUNT_LOGIN', 'sfci')
CI_KEYFILE = os.environ.get('GERRIT_SSH_KEY', '/home/jgriffith/.ssh/sfci_rsa')
OS_REVIEW_HOST = os.environ.get('GERRIT_HOST', 'review.openstack.org')
OS_REVIEW_HOST_PORT = os.environ.get('GERRIT_PORT', 29418)
PROJECT = os.environ.get('CI_PROJECT', 'cinder')
CI_NAME = 'SolidFire-'

event_queue = deque()

class InstanceBuildException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

def _filter_cinder_events(event):

    if (event.get('type', 'nill') == 'comment-added' and
        'Verified+1' in event['comment'] and
        PROJECT in event['change']['project']):
        if event['author']['username'] == 'jenkins':
            print ('Adding review id %s to job queue...' %
                   event['change']['number'])
            return event
    else:
        return None


class JobThread(Thread):
    """ Thread to process the gerrit events. """

    def _upload_results_to_web(self):
        pass

    def _post_results_to_gerrit(self, log_location, passed, commit_id):
        #ssh -p 29418 USERNAME@review.openstack.org gerrit review -m '"Test failed on MegaTestSystem <http://megatestsystem.org/tests/1234>"' --verified=-1 c0ff33
        cmd = ""
        if passed:
            cmd = '"Test sfci-dsvm-volume passed on SolidFire CI System %s" --verified=+1 %s' % (log_location, commit_id)
        else:
            cmd = '"Test sfci-dsvm-volume failed on SolidFire CI System %s" --verified=-1 %s' % (log_location, commit_id)

        self.username = CI_ACCOUNT
        self.key_file = CI_KEYFILE
        self.host = OS_REVIEW_HOST
        self.port = OS_REVIEW_HOST_PORT
        print ('Connecting to gerrit stream with %s@%s:%d '
               'using keyfile %s' % (self.username,
                                     self.host,
                                     self.port,
                                     self.key_file))

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(self.host,
                             self.port,
                             self.username,
                             key_filename=self.key_file)
        except paramiko.SSHException as e:
            print e
            sys.exit(1)

        self.stdin, self.stdout, self.stderr =\
            self.ssh.exec_command(cmd)


    def run(self):
        while True:
            if not event_queue:
                time.sleep(60)
                print "loop...debug"
            else:
                event = event_queue.popleft()
                # Launch instance, run tempest etc etc etc
                name = ('review-%s' % event['change']['number'])
                try:
                    result = executor.just_doit(event['patchSet']['ref'])
                    print "Results from tempest: %s" % result
                except InstanceBuildException:
                    pass

                print "Completed %s-dsvm-full" % CI_NAME
                print "Events in queue: %s" % len(event_queue)


class GerritEventStream(object):
    def __init__(self, *args, **kwargs):

        self.username = CI_ACCOUNT
        self.key_file = CI_KEYFILE
        self.host = OS_REVIEW_HOST
        self.port = OS_REVIEW_HOST_PORT
        print ('Connecting to gerrit stream with %s@%s:%d '
               'using keyfile %s' % (self.username,
                                     self.host,
                                     self.port,
                                     self.key_file))

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(self.host,
                             self.port,
                             self.username,
                             key_filename=self.key_file)
        except paramiko.SSHException as e:
            print e
            sys.exit(1)

        self.stdin, self.stdout, self.stderr =\
            self.ssh.exec_command("gerrit stream-events")

    def __iter__(self):
        return self

    def next(self):
        return self.stdout.readline()

def process_options():
    config = {}
    usage = "usage: %prog [options]\nos_ci.py."
    parser = OptionParser(usage, version='%prog 0.1')

    parser.add_option('-n', '--num-threads', action='store',
                      type='int',
                      default=2,
                      dest='number_of_worker_threads',
                      help='Number of job threads to run (default = 2).')
    parser.add_option('-m', action='store_true',
                      dest='event_monitor_only',
                      help='Just monitor Gerrit stream, dont process events.')
    (options, args) = parser.parse_args()
    return options

if __name__ == '__main__':
    global event_queue
    options = process_options()

    for i in xrange(options.number_of_worker_threads):
        JobThread().start()

    while True:
        events = GerritEventStream('sfci')
        for event in events:
            event = json.loads(event)
            valid_event = _filter_cinder_events(event)
            if valid_event:
                if not options.event_monitor_only:
                    print "Adding event to queue..."
                    event_queue.append(valid_event)
