#!/usr/bin/python

import datetime

from model.db_engine import reviews
from model.db_engine import revisions

if __name__ == "__main__":
    try:
        q = reviews.insert(gerrit_url='https://review.openstack.org/#/c/147738/',
                           project_name='Cinder',
                           branch='master',
                           id=10000,
                           author='me',
                           author_email='me@email.com',
                           created_at=datetime.datetime.now())
        q.execute()
    except Exception as ex:
        print ex
        pass

    r = revisions.insert(patchset_number='2',
                         review=10000,
                         sos_success=True,
                         gate_success=True,
                         setup_failure=False,
                         created_at=datetime.datetime.now())
    r.execute()
