#!/usr/bin/python

import peewee as pw
from model.db_engine import reviews
from model.db_engine import revisions

if __name__ == "__main__":
    try:
        reviews.create_table()
    except pw.OperationalError:
        print "Already exists"
    try:
        revisions.create_table()
    except pw.OperationalError:
        print "Already exists"
