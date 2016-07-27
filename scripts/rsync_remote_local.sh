#!/bin/sh
# updatedb.sh executes the script dodump on a remote server
# dodump creates a temporary docker container that dumps a servers database
# into this servers data folder within odoo_instances
# parameters:
# $1 : site name
# $2 : server url
# $3 : remote_path like /root/odoo_instances
# $4 : login name on remote server
echo ssh $4@$2 'bash -s' < scripts/dodump.sh $1
ssh $4@$2 'bash -s' < scripts/dodump.sh $1
echo rsync -avzC --delete $4@$2:/$3/$1/filestore/ $1/filestore/
rsync -avzC --delete $4@$2:/$3/$1/filestore/ $1/filestore/
echo rsync -avzC --delete $4@$2:/$3/$1/dump/ $1/dump/
rsync -avzC --delete $4@$2:/$3/$1/dump/ $1/dump/
