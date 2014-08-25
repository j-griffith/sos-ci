#!/usr/bin/python

from collections import deque
import json
from optparse import OptionParser
import os
import paramiko
import sys
from threading import Thread
import time

import instance


# CI related variables
CI_ACCOUNT = os.environ.get('CI_ACCOUNT_LOGIN', 'sfci')
CI_KEYFILE = os.environ.get('GERRIT_SSH_KEY', '/home/jgriffith/.ssh/sfci_rsa')
OS_REVIEW_HOST = os.environ.get('GERRIT_HOST', 'review.openstack.org')
OS_REVIEW_HOST_PORT = os.environ.get('GERRIT_PORT', 29418)
IMAGE_ID = os.environ.get('CI_IMAGE_ID', '39abf4bc-29a8-4b84-963f-b1a1890ca6bf')
FLAVOR = os.environ.get('DEFAULT_FLAVOR', '4')
PROJECT = os.environ.get('CI_PROJECT', 'cinder')
KEY_NAME = os.environ.get('DEFAULT_OS_KEYFILE', 'default_key')
CI_NAME = 'SolidFire-'

event_queue = deque()

class InstanceBuildException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

def _filter_cinder_events(event):
    return event

    if (event.get('type', 'nill') == 'comment-added' and
        'Verified+1' in event['comment']):
        # add: PROJECT in event['change']['project'] above
        if event['author']['username'] == 'jenkins':
            print ('Adding review id %s to job queue...' %
                   event['change']['number'])
            return event
    else:
        return None


class JobThread(Thread):
    """ Thread to process the gerrit events. """
    def _launch_instance(self, name):
        test_instance = instance.Instance(name)
        timeout = 90
        if test_instance.wait_for_ready(timeout=timeout):
            return test_instance
        else:
            print "Instance failed to build after 90 seconds!!"
            raise InstanceBuildException('Instance failed to become ready after %s seconds' % timeout)

    def _delete_instance(self, instance):
        instance.delete_instance()


    def _run_tempest_suite(self, instance, event):
        pass

    def _publish_results_to_web(self, instance):
        pass

    def _publish_results_to_gerrit(self, event, result):
        pass

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
                    instance = self._launch_instance(name)
                    # TODO: Run dsvm-full
                    time.sleep(60)
                except InstanceBuildException:
                    pass

                self._delete_instance(instance)
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
