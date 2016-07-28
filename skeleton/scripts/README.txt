README.txt
----------
Files in scripts/

backup_scheduler.py
-------------------
copied from a backup module. not yet used

updatedb.sh & dodump.sh
-----------------------
these two shell scripts work together to dump the remote database
into a file skeleton.sh and copy it over the net into the local file
sql_dumps/skeleton.sql 

__init__.py
-----------
it just exists

restore_to_db.py
----------------
This python scripts drops/creates the database and dumps the data into it
that it finds in sql_dumps/skeleton.sql 

database name and login info it gets from etc/openerp.conf


server.py session.py
--------------------
not used just now
