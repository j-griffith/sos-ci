# We'll move the actual work of deploying devstack and running tempest here
# Same idea, make it a class that can be over-ridden with your own version of
# tool chain.

import fileinput
import paramiko
from scp import SCPClient
import sys


def just_doit(ip, keyfile, patchset_ref):
    """ Do the dirty work.

    Runs stack.sh using the specified patchset, uploads
    logs/results to webserver.
    """

    # patchset_ref is valid_event['patchSet']['ref']
    # ( refs/changes/21/111421/7 )
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh = ssh_client.connect(ip,
                                 login='ubuntu',
                                 key_filename=keyfile)
        scp = SCPClient(ssh.get_transport())
    except paramiko.SSHException as e:
        print e
        sys.exit(1)
    for line in fileinput.FileInput('./local.conf.template', inplace=1):
        if 'CINDER_BRANCH' in line:
            line = line.replace('CINDER_BRANCH=MASTER',
                                'CINDER_BRANCH=%s' %
                                (patchset_ref))
    scp.put('./scripts/local.conf.template', '~/devstack/local.conf')
    scp.put('./scripts/upload_logs.sh', '~/')
    stdin, stdout, stderr = \
        ssh.exec_command('cd ~/devstack && ./stack.sh')
    stdin, stdout, stderr = \
        ssh.exec_command('cd /opt/stack/tempest && ./tools/bash '
                         './tools/pretty_tox.sh --concurrency=4 '
                         '| tee -a console.log.out')
    status = 'passed'
    stdin, stdout, stderr = \
        ssh.exec_command('bash ~/upload_logs.sh %s %s' %
                         (patchset_ref, status))
