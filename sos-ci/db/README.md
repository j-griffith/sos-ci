# DB setup

If you select the enable_database option, you'll need
to setup the db of your choice using the files in this
directory.

We're using [peewee](https://peewee.readthedocs.org/en/latest/) for our db
interface to python.  Peewee is a light weight version of sqlalchemy, and offers
the ability to work with multiple sql type databases.

In ./model/db_engine.py you'll find our schema as well as the needed info
to access the DB (type, location, login and pass).  Make sure you modify these
to fit your actual deployment, and of course don't forget to change the db engine
settings if you're not using MySQL.

## Setup
Once you've setup a db and installed peewee (pip install peewee), you are ready
to create the tables in the DB.  Just use the create_tables.py script in this
directory.  NOTE: peewee won't create the DB for you, you'll have to do that
before you run the script to create the tables.

That's really about it, you can inspect the db_engine.py file to see what I've
chosen for the initial schema, suggestions are welcome.


## Why
A big problem with third party CI in my opinion right now is reliability.  There
are plenty of systems running (some Vendors have 5 or 6), but the results are
so unreliable that most of us rarely look at them any more.

The idea here is to actually collect data on a CI system, store it in a database
and setup queiries to publish statistics on how it's doing.  The goal is to publish
a dashboard (on the same server we push results to) that shows the following items
for this particular CI system:
  1. Number of patches succesfully run by Gate/Jenkins
  2. Number of patches succesfully run by our sos-ci system
  3. Number of runs that were succesful/failed
  4. How many runs failed due to setup failure vs test failure

