import subprocess

# We'll move the actual work of deploying devstack and running tempest here
# Same idea, make it a class that can be over-ridden with your own version of
# tool chain.



def just_doit(patchset_ref):
    """ Do the dirty work. """

    # patchset_ref is valid_event['patchSet']['ref']
    # ( refs/changes/21/111421/7 )
    ref_name = patchset_ref.replace('/', '-')
    vars = "os_login=admin os_password=solidfire os_tenant_name=demo"
    vars += " auth_url=http://172.16.140.247:5000/v2.0 flavor_id=100 key_name=bdr77-default-key"
    vars += " instance_name=%s image_id=1f91f80e-9d0b-4466-b79c-65ef4b09a869" % ref_name
    vars += " patchset_ref=%s" % patchset_ref
    cmd = '/usr/local/bin/ansible-playbook --extra-vars \"%s\" ./ansible/sites.yml' % vars
    #cmd = 'ls'

    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    output = p.stdout.read()
    print output
    #process = subprocess.Popen(cmd,
    #                           stdout=subprocess.PIPE,
    #                           stderr=subprocess.PIPE)
    #results = process.communicate()[0]
    #import pdb;pdb.set_trace()
    #output = process.stdout.read()
    #print output

