import os
import subprocess

""" EZ-PZ just call our ansible playbook.

Would be great to write a playbook runner at some point, but
this is super straight forward and it works so we'll use it for now.

"""



def just_doit(patchset_ref):
    """ Do the dirty work, or let ansible do it. """

    # patchset_ref is valid_event['patchSet']['ref']
    # ( refs/changes/21/111421/7 )
    ref_name = patchset_ref.replace('/', '-')
    vars = "instance_name=%s" % (ref_name)
    vars += " patchset_ref=%s" % patchset_ref
    cmd = '/usr/local/bin/ansible-playbook --extra-vars \"%s\" ./ansible/sites.yml' % vars

    ansible_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = ansible_proc.communicate()[0]

    vars = "source_file=%s" % (ref_name)
    cmd = '/usr/local/bin/ansible-playbook --extra-vars \"%s\" ./ansible/publish.yml' % vars
    # This output is actually the ansible output
    # should fix this up and have it just return the status
    # and the tempest log that we xfrd over
    ansible_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output += ansible_proc.communicate()[0]

    success = False
    hash_id = None
    console_log = './logs/%s.console' % ref_name
    if os.path.isfile(console_log):
        if 'Failed: 0' in open(console_log).read():
            success = True

        # We grab the abbreviated sha from the first line of the
        # console.out file
        with open('./logs/%s.console' % ref_name) as f:
            first_line=f.readline()
        print "Attempting to parse: %s" % first_line
        hash_id = first_line.split()[1]

    # Finally, delete the instance regardless of pass/fail
    # NOTE it's moved out of tasks here otherwise it won't
    # run if preceeded by a failure
    vars = "instance_name=%s" % (ref_name)
    vars += " patchset_ref=%s" % patchset_ref
    cmd = '/usr/local/bin/ansible-playbook --extra-vars \"%s\" ./ansible/teardown.yml' % vars

    ansible_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = ansible_proc.communicate()[0]

    return (hash_id, success, output)
