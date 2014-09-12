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

    with open('./logs/%s.console' % ref_name) as file:
        commit_id = file.readline()

    success = False
    if 'Failed: 0' in open('./logs/%s.console' % ref_name).read():
        success = True

    return (success, commit_id, output)
