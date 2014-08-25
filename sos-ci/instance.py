import os
import time

from novaclient.v1_1 import client as novaclient


class Instance(object):
    """ Class to handle the actually do the work.

    This class provides the basics for creating an instance,
    setting up devstack and running tempest.  The base class
    here just uses novaclient and simple paramiko/ssh, you
    can easily override this if you like to choose your favorite
    orchestration tools (say ansible with nova-compute module,
    vagrant with openstack-provider, salt etc).
    """

    def __init__(self, name, *args, **kwargs):
        self.os_user = os.getenv('OS_USERNAME')
        self.os_pass = os.getenv('OS_PASSWORD')
        self.os_tenant_id = os.getenv('OS_TENANT_NAME')
        self.os_auth_url = os.getenv('OS_AUTH_URL')
        self.default_flavor = kwargs.get('instance_flavor', 4)
        self.key_name = kwargs.get('key_name', 'default_key')
        self.default_image_id =\
            kwargs.get('image_id',
                       '39abf4bc-29a8-4b84-963f-b1a1890ca6bf')
        self.nova_client = novaclient.Client(self.os_user,
                                             self.os_pass,
                                             self.os_tenant_id,
                                             self.os_auth_url)
        self.instance = self._boot_instance(name)

    def _boot_instance(self, name):

        # FIXME(jdg): Need to consider error handling here
        # do we have quota?  Did something go out to lunch?
        return self.nova_client.servers.create(name,
                                               self.default_image_id,
                                               self.default_flavor,
                                               key_name=self.key_name)

    def wait_for_ready(self, timeout=90):
        while timeout > 0:
            self.instance = self.nova_client.servers.get(self.instance.id)
            if self.instance.status == 'ACTIVE':
                return True
            time.sleep(1)
        return False

    def get_current_status(self):
        self.instance = self.nova_client.servers.get(self.instance.id)
        return self.instance.status

    def deploy_devstack(self):
        pass

    def upload_results(self, destination):
        status = 0
        return status

    def delete_instance(self):
        self.instance = self.nova_client.servers.delete(self.instance.id)

    def run_tempest(self, options):
        pass
