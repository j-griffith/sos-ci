#!/usr/bin/python

from collections import deque
import json
from optparse import OptionParser
import os
import paramiko
import subprocess
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
pipeline = deque()


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

    def _post_results_to_gerrit(self, log_location, passed, commit_id):
        #ssh -p 29418 USERNAME@review.openstack.org gerrit review -m '"Test failed on MegaTestSystem <http://megatestsystem.org/tests/1234>"' --verified=-1 c0ff33
        cmd = "gerrit review -m "
        failed = False
        if commit_id:
            if passed:
                #cmd = """'"Test sfci-dsvm-volume passed on SolidFire CI System %s"' --verified +1 %s""" % (log_location, commit_id)
                cmd = cmd + """'"* solidfire-dsvm-volume %s : SUCCESS "' %s""" % (log_location, commit_id)
            else:
                cmd = cmd + """'"* solidfire-dsvm-volume %s : FAILED "' %s""" % (log_location, commit_id)
                failed = True
        else:
            commit_id = 'failed'
            failed = True

        with open('/home/jgriffith/sos_ci_results.dat', 'a') as f:
            f.write('%s\n' % cmd)
        #return
        if failed:
            return

        self.username = CI_ACCOUNT
        self.key_file = CI_KEYFILE
        self.host = OS_REVIEW_HOST
        self.port = OS_REVIEW_HOST_PORT
        print ('Connecting to gerrit for voting %s@%s:%d '
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

        print ('Issue vote: %s' % cmd)
        self.stdin, self.stdout, self.stderr =\
            self.ssh.exec_command(cmd)


    def run(self):
        while True:
            if not event_queue:
                time.sleep(60)
                print "loop...debug"
            else:
                event = event_queue.popleft()

                # Add a goofy pipeline queue so we know
                # not only when nothing is in the queue
                # but when nothings outstanding so we can
                # run cleanup on the backend device
                pipeline.append(valid_event)

                # Launch instance, run tempest etc etc etc
                name = ('review-%s' % event['change']['number'])
                patchset_ref = event['patchSet']['ref']
                try:
                    commit_id, success, output = \
                        executor.just_doit(event['patchSet']['ref'])

                except InstanceBuildException:
                    pass

                print "Completed %s-dsvm-full" % CI_NAME
                url_name = patchset_ref.replace('/', '-')
                log_location = 'http://54.164.167.86/solidfire-ci-logs/%s' % url_name
                self._post_results_to_gerrit(log_location, success, commit_id)
                #print "Events in queue: %s" % len(event_queue)
                #self._post_results_to_gerrit('http://54.164.167.86/solidfire-ci-logs/%s' % 'foo',
                #                             success,
                #                             commit_id)
                try:
                    pipeline.remove(valid_event)
                except ValueError:
                    pass

                # So if there's nothing in event_queue and nothing in progress
                # should be a great time to delete and purge everything on the
                # backend device
                if len(event_queue) == 0 and len(pipeline) == 0:
                    cmd = '/usr/local/bin/ansible-playbook ./ansible/cleanup_test_cluster.yml'
                    ansible_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                    ansible_proc.communicate()[0]


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
