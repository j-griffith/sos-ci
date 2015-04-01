#!/usr/bin/python

from email.mime.text import MIMEText
from collections import deque
import json
from optparse import OptionParser
import os
import paramiko
import shutil
import subprocess
import sys
from threading import Thread
import time

from iniparse import INIConfig
from subunit2sql import read_subunit
from subunit2sql import shell

import executor
import log

fdir = os.path.dirname(os.path.realpath(__file__))
conf_dir = os.path.dirname(fdir)
cfg = INIConfig(open(conf_dir + '/sos-ci.conf'))

# Misc settings
DATA_DIR =\
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/data'
if cfg.Data.data_dir:
    DATA_DIR = cfg.Data.data_dir

logger = log.setup_logger(DATA_DIR + '/os-ci.log')
event_queue = deque()
pipeline = deque()


class InstanceBuildException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


def _is_my_ci_recheck(event):
    if (event.get('type', 'nill') == 'comment-added' and
            cfg.AccountInfo.recheck_string in event['comment'] and
            cfg.AccountInfo.project_name == event['change']['project'] and
            event['change']['branch'] == 'master'):
        logger.info('Detected recheck request for event: %s', event)
        return True
    return False


def _is_my_ci_master(event):
    if (event.get('type', 'nill') == 'comment-added' and
            'Verified+1' in event['comment'] and
            cfg.AccountInfo.project_name == event['change']['project']):
        if event['author']['username'] == 'jenkins':
            if event['change']['branch'] != 'master':
                logger.info('Not testing changes outside of master '
                            'yet (branch=%s).',
                            event['change']['branch'])
            else:
                logger.info('Detected valid event: %s', event)
                return True
    return False


def _filter_cinder_events(event):
    if _is_my_ci_recheck(event) or _is_my_ci_master(event):
        logger.info('Adding review id %s to job queue...' %
                    event['change']['number'])

        # One log to act as a data store, and another just to look at
        with open(DATA_DIR + '/valid-event.log', 'a') as f:
            json.dump(event, f)
            f.write('\n')
        with open(DATA_DIR + '/pretty-event.log', 'a') as f:
            json.dump(event, f, indent=2)
        return event
    else:
        return None


def _send_notification_email(subject, msg):
    if cfg.Email.enable_notifications:
        msg = MIMEText(msg)
        msg["From"] = cfg.Email.from_address
        msg["To"] = cfg.Email.to_address
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
        msg = 'Commit: %s\nLogs: %s\n' % (commit_id, log_location)
        if passed:
            subject += " %s SUCCESS" % cfg.AccountInfo.ci_name
            msg += "Result: SUCCESS"
            cmd += """"* %s %s : SUCCESS " %s""" % \
                   (cfg.AccountInfo.ci_name, log_location, commit_id)
            logger.debug("Created success cmd: %s", cmd)
        else:
            subject += " sf-dsvm FAILED"
            msg += "Result: FAILED"
            cmd += """"* %s %s : FAILURE " %s""" % \
                   (cfg.AccountInfo.ci_name, log_location, commit_id)
            logger.debug("Created failed cmd: %s", cmd)

        logger.debug('Issue notification email, '
                     'Subject: %(subject)s, %(msg)s',
                     {'subject': subject, 'msg': msg})

        _send_notification_email(subject, msg)

        logger.debug('Connecting to gerrit for voting '
                     '%(user)s@%(host)s:%(port)d '
                     'using keyfile %(key_file)s',
                     {'user': cfg.AccountInfo.ci_account,
                      'host': cfg.AccountInfo.gerrit_host,
                      'port': int(cfg.AccountInfo.gerrit_port),
                      'key_file': cfg.AccountInfo.gerrit_ssh_key})

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(cfg.AccountInfo.gerrit_host,
                             int(cfg.AccountInfo.gerrit_port),
                             cfg.AccountInfo.ci_account,
                             key_filename=cfg.AccountInfo.gerrit_ssh_key)
        except paramiko.SSHException as e:
            logger.error('%s', e)
            sys.exit(1)

        logger.info('Issue vote: %s', cmd)
        self.stdin, self.stdout, self.stderr =\
            self.ssh.exec_command(cmd)

    def _run_subunit2sql(self, results_dir, ref_name, commit_id):
        if not cfg.DataBase.enable_subunit2sql:
            logger.info('DataBase.enable_subunit2sql is not enabled, '
                        'skipping data base operations')
            return

        subunit_file = results_dir + '/' + ref_name + '/testrepository.subunit'
        shell.parse_args([])
        # NOTE(mtreinish) The use of CONF below is just how config is set in
        # the subunit2sql python API
        shell.CONF.set_override('connection',
                                cfg.DataBase.database_connection_string,
                                group='database')
        shell.CONF.set_override('artifacts', os.path.join(results_dir,
                                                          ref_name))
        metadata = {'ref_name': ref_name, 'commit_ref': commit_id}
        shell.CONF.set_override('run_meta', metadata)
        with open(subunit_file, 'r') as sub_file:
            stream = read_subunit.ReadSubunit(sub_file)
            shell.process_results(stream.get_results())
        return

    def run(self):
        counter = 60
        while True:
            counter -= 1
            event_queue
            if not event_queue:
                if counter <= 1:
                    logger.debug('Queue is empty, '
                                 'checking every 60 seconds...')
                    counter = 60
                time.sleep(60)
            else:
                event = event_queue.popleft()
                logger.debug("Processing event from queue:\n%s", event)

                # Add a goofy pipeline queue so we know
                # not only when nothing is in the queue
                # but when nothings outstanding so we can
                # run cleanup on the backend device
                pipeline.append(valid_event)

                # Launch instance, run tempest etc etc etc
                patchset_ref = event['patchSet']['ref']
                revision = event['patchSet']['revision']
                logger.debug('Grabbed revision from event: %s', revision)

                ref_name = patchset_ref.replace('/', '-')
                results_dir = DATA_DIR + '/' + ref_name

                # This might be a recheck, if so we've presumably
                # run things once and published, so delete the
                # local copy and run it again
                if os.path.isdir(results_dir):
                    shutil.rmtree(results_dir)
                os.mkdir(results_dir)

                try:
                    commit_id, success, output = \
                        executor.just_doit(event['patchSet']['ref'],
                                           results_dir)
                    logger.info('Completed just_doit: %(commit)s, '
                                '%(success)s, %(output)s',
                                {'commit': commit_id,
                                 'success': success,
                                 'output': output})

                except InstanceBuildException:
                    logger.error('Received InstanceBuildException...')
                    pass

                if commit_id is None:
                    commit_id = revision

                logger.info("Completed %s", cfg.AccountInfo.ci_name)
                url_name = patchset_ref.replace('/', '-')
                log_location = cfg.Logs.log_dir + '/' + url_name
                self._post_results_to_gerrit(log_location, success, commit_id)
                self._run_subunit2sql(results_dir, ref_name, commit_id)

                try:
                    pipeline.remove(valid_event)
                except ValueError:
                    pass


class GerritEventStream(object):
    def __init__(self, *args, **kwargs):

        logger.debug('Connecting to gerrit stream with '
                     '%(user)s@%(host)s:%(port)d '
                     'using keyfile %(key_file)s',
                     {'user': cfg.AccountInfo.ci_account,
                      'host': cfg.AccountInfo.gerrit_host,
                      'port': int(cfg.AccountInfo.gerrit_port),
                      'key_file': cfg.AccountInfo.gerrit_ssh_key})

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(cfg.AccountInfo.gerrit_host,
                             int(cfg.AccountInfo.gerrit_port),
                             cfg.AccountInfo.ci_account,
                             key_filename=cfg.AccountInfo.gerrit_ssh_key)
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
                      default=3,
                      dest='number_of_worker_threads',
                      help='Number of job threads to run (default = 3).')
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

    while True:
        events = GerritEventStream('sfci')
        for event in events:
            try:
                event = json.loads(event)
            except Exception as ex:
                logger.error('Failed json.loads on event: %s', event)
                logger.exception(ex)
                break
            with open(DATA_DIR + '/received-events.log', 'a') as f:
                json.dump(event, f)
                f.write('\n')
            valid_event = _filter_cinder_events(event)
            if valid_event:
                logger.debug('Identified valid event, sending to queue...')
                if not options.event_monitor_only:
                    logger.debug("Adding event to queue:%s\n", valid_event)
                    event_queue.append(valid_event)
