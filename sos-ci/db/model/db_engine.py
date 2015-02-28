#!/usr/bin/python

import datetime
import peewee as pw

db = pw.MySQLDatabase('sosci', host='localhost', user='root', password='secrete')
db.connect()

class MySQLModel(pw.Model):
    class Meta:
            database = db

class reviews(MySQLModel):
    id = pw.IntegerField(primary_key=True)
    gerrit_url = pw.CharField()
    project = pw.CharField(default='cinder')
    branch = pw.CharField(default='master')
    topic = pw.CharField()
    created_at = pw.DateTimeField(default=datetime.datetime.now)

class revisions(MySQLModel):
    patchset_number = pw.IntegerField()
    patchset_ref = pw.CharField()
    review_id = pw.ForeignKeyField(reviews, related_name='revisions')
    sos_success = pw.BooleanField(default=False)
    log_logcation=pw.CharField(default=None)
    executed_sos=pw.BooleanField(default=False)
    created_at = pw.DateTimeField(default=datetime.datetime.now)
