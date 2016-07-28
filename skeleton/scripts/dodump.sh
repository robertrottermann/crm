#!/bin/sh
# this script dumps the database urgestein into the file urgestein.sql
# it is called by updatedb.sh and executed on the remote computer
PGPASSWORD=$3 pg_dump -Fc $1 > $1.dmp 