#!/usr/bin/python

from email.mime.text import MIMEText
from collections import deque
import json
import logging
import logging.handlers
from optparse import OptionParser
import os
import paramiko
import subprocess
import sys
from threading import Thread
import time

import executor

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] "
                                 "[%(levelname)-5.5s]  %(message)s")

file_handler =\
    logging.handlers.RotatingFileHandler('/home/jgriffith/sos-ci.log',
                                         maxBytes=1048576,
                                         backupCount=2,)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logFormatter)
logger.addHandler(console_handler)


# CI Account  related variables
CI_ACCOUNT = os.environ.get('CI_ACCOUNT_LOGIN', 'sfci')
CI_KEYFILE = os.environ.get('GERRIT_SSH_KEY', '/home/jgriffith/.ssh/sfci_rsa')
OS_REVIEW_HOST = os.environ.get('GERRIT_HOST', 'review.openstack.org')
OS_REVIEW_HOST_PORT = os.environ.get('GERRIT_PORT', 29418)
PROJECT = os.environ.get('CI_PROJECT', 'cinder')
CI_NAME = 'SolidFire-'

# Email Notifications
ENABLE_EMAIL_NOTIFICATIONS = True
FROM_EMAIL_ADDRESS = "sfci@bdr76.solidfire.com"
TO_EMAIL_ADDRESS = "john.griffith@solidfire.com"

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
            logging.info('Adding review id %s to job queue...' %
                         event['change']['number'])
            return event
    else:
        return None


def _send_notification_email(subject, msg):
    if ENABLE_EMAIL_NOTIFICATIONS:
        msg = MIMEText(msg)
        msg["From"] = FROM_EMAIL_ADDRESS
        msg["To"] = TO_EMAIL_ADDRESS
        msg["Subject"] = subject
        p = subprocess.Popen(["/usr/sbin/sendmail", "-t"],
                             stdin=subprocess.PIPE)
        p.communicate(msg.as_string())


class JobThread(Thread):
    """ Thread to process the gerrit events. """

    def _post_results_to_gerrit(self, log_location, passed, commit_id):
        logger.debug("Post results to gerrit using %(location)s\n "
                     "passed: %(passed)s\n commit_id: %(commit_id)s\n",
                     {'location': log_location,
                      'passed': passed,
                      'commit_id': commit_id})

        cmd = "gerrit review -m "
        subject = ''
        msg = ''
        logger.debug('Building gerrit review message...')
        msg = 'Commit: %s\nLogs: %s\n' % (log_location, commit_id)
        if passed:
            subject += " sf-dsvm SUCCESS"
            msg += "Result: SUCCESS"
            cmd += """"* solidfire-dsvm-volume %s : SUCCESS " %s""" % \
                   (log_location, commit_id)
            logger.debug("Created success cmd: %s", cmd)
        else:
            subject += " sf-dsvm FAILED"
            msg += "Result: FAILED"
            cmd += """"* solidfire-dsvm-volume %s : FAILED " %s""" % \
                   (log_location, commit_id)
            logger.debug("Created failed cmd: %s", cmd)

        msg += "\nLOGS: log_location"
        logger.debug('Issue notification email, '
                     'Subject: %(subject)s, %(msg)s',
                     {'subject': subject, 'msg': msg})

        _send_notification_email(subject, msg)
        with open('/home/jgriffith/sos_ci_results.dat', 'a') as f:
            f.write('%s\n' % cmd)

        self.username = CI_ACCOUNT
        self.key_file = CI_KEYFILE
        self.host = OS_REVIEW_HOST
        self.port = OS_REVIEW_HOST_PORT
        logger.debug('Connecting to gerrit for voting '
                     '%(user)s@%(host)s:%(port)d '
                     'using keyfile %(key_file)s',
                     {'user': self.username,
                      'host': self.host,
                      'port': self.port,
                      'key_file': self.key_file})

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(self.host,
                             self.port,
                             self.username,
                             key_filename=self.key_file)
        except paramiko.SSHException as e:
            logger.error('%s', e)
            sys.exit(1)

        logger.info('Issue vote: %s', cmd)
        self.stdin, self.stdout, self.stderr =\
            self.ssh.exec_command(cmd)

    def run(self):
        while True:
            event_queue
            if not event_queue:
                logging.debug('queue is empty, sleep for 60 '
                              'seconds and check again...')
                time.sleep(60)
            else:
                event = event_queue.popleft()
                logging.debug("Processing event from queue:\n%s", event)

                # Add a goofy pipeline queue so we know
                # not only when nothing is in the queue
                # but when nothings outstanding so we can
                # run cleanup on the backend device
                pipeline.append(valid_event)

                # Launch instance, run tempest etc etc etc
                patchset_ref = event['patchSet']['ref']
                revision = event['patchSet']['revision']

                try:
                    commit_id, success, output = \
                        executor.just_doit(event['patchSet']['ref'])
                    logger.info('Completed just_doit: %(commit)s, '
                                '%(success)s, %(output)s',
                                {'commit': commit_id,
                                 'success': success,
                                 'output': output})

                except InstanceBuildException:
                    logger.error('Received InstanceBuildException...')
                    pass

                if not commit_id:
                    commit_id = revision

                logger.info("Completed %s-dsvm-full", CI_NAME)
                url_name = patchset_ref.replace('/', '-')
                log_location = ('http://54.164.167.86/solidfire-ci-logs/%s' %
                                url_name)
                self._post_results_to_gerrit(log_location, success, commit_id)
                try:
                    pipeline.remove(valid_event)
                except ValueError:
                    pass


class GerritEventStream(object):
    def __init__(self, *args, **kwargs):

        self.username = CI_ACCOUNT
        self.key_file = CI_KEYFILE
        self.host = OS_REVIEW_HOST
        self.port = OS_REVIEW_HOST_PORT
        logger.debug('Connecting to gerrit stream with '
                     '%(user)s@%(host)s:%(port)d '
                     'using keyfile %(key_file)s',
                     {'user': self.username,
                      'host': self.host,
                      'port': self.port,
                      'key_file': self.key_file})

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(self.host,
                             self.port,
                             self.username,
                             key_filename=self.key_file)
        except paramiko.SSHException as e:
            logger.error('%s', e)
            sys.exit(1)

        self.stdin, self.stdout, self.stderr =\
            self.ssh.exec_command("gerrit stream-events")

    def __iter__(self):
        return self

    def next(self):
        return self.stdout.readline()


def process_options():
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
    event_queue = deque()
    options = process_options()

    for i in xrange(options.number_of_worker_threads):
        JobThread().start()
    JobThread().start()

    while True:
        events = GerritEventStream('sfci')
        for event in events:
            try:
                event = json.loads(event)
            except Exception as ex:
                logging.error('Failed json.loads on event: %s', event)
                logging.exception(ex)
                break
            valid_event = _filter_cinder_events(event)
            if valid_event:
                if not options.event_monitor_only:
                    logger.debug("Adding event to queue:%s\n", valid_event)
                    event_queue.append(valid_event)
