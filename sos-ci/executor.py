import os
import subprocess

import log

from iniparse import INIConfig

fdir = os.path.dirname(os.path.realpath(__file__))
conf_dir = os.path.dirname(fdir)
cfg = INIConfig(open(conf_dir + '/sos-ci.conf'))

""" EZ-PZ just call our ansible playbook.

Would be great to write a playbook runner at some point, but
this is super straight forward and it works so we'll use it for now.

"""

def just_doit(patchset_ref):
    """ Do the dirty work, or let ansible do it. """

    ref_name = patchset_ref.replace('/', '-')
    logger = log.setup_logger(ref_name, '/home/jgriffith/sos-ci/data/logs')
    logger.debug('Attempting ansible tasks on ref-name: %s', ref_name)
    vars = "instance_name=%s" % (ref_name)
    vars += " patchset_ref=%s" % patchset_ref
    cmd = '/usr/local/bin/ansible-playbook --extra-vars '\
          '\"%s\" %s/run_ci.yml' % (vars, cfg.Ansible.ansible_dir)

    logger.debug('Running ansible run_ci command: %s', cmd)
    ansible_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = ansible_proc.communicate()[0]
    logger.debug('Response from ansible: %s', output)

    # FIXME(jdg): Currently if the build task (or tasks) fail
    # we don't publish anything, add some logic here to
    # upload the ansible logs to the web server so one can
    # view the reason why something fails

    vars = "source_file=%s" % (ref_name)
    cmd = '/usr/local/bin/ansible-playbook --extra-vars '\
          '\"%s\" %s/publish.yml' %  (vars, cfg.Ansible.ansible_dir)
    logger.debug('Running ansible publish command: %s', cmd)

    # This output is actually the ansible output
    # should fix this up and have it just return the status
    # and the tempest log that we xfrd over
    ansible_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output += ansible_proc.communicate()[0]
    logger.debug('Response from ansible: %s', output)

    success = False
    hash_id = None
    console_log = './logs/%s.console' % ref_name
    logger.debug('Looking for console log at: %s', console_log)
    if os.path.isfile(console_log):
        logger.debug('Found the console log...')
        if 'Failed: 0' in open(console_log).read():
            logger.debug('Evaluated run as successful')
            success = True

        logger.info('Status from console logs: %s', success)
        # We grab the abbreviated sha from the first line of the
        # console.out file
        with open('./logs/%s.console' % ref_name) as f:
            first_line = f.readline()
        print "Attempting to parse: %s" % first_line
        hash_id = first_line.split()[1]

    # Finally, delete the instance regardless of pass/fail
    # NOTE it's moved out of tasks here otherwise it won't
    # run if preceeded by a failure
    vars = "instance_name=%s" % (ref_name)
    vars += " patchset_ref=%s" % patchset_ref
    cmd = '/usr/local/bin/ansible-playbook --extra-vars '\
          '\"%s\" %s/teardown.yml' %  (vars, cfg.Ansible.ansible_dir)

    logger.debug('Running ansible teardown command: %s', cmd)
    ansible_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = ansible_proc.communicate()[0]

    return (hash_id, success, output)
