#!/bin/sh
# updatedb.sh executes the script dodump on a remote server
# dodump creates a temporary docker container that dumps a servers database
# into this servers data folder within odoo_instances
# parameters:
# $1 : site name
# $2 : server url
# $3 : remote_path like /root/odoo_instances
# $4 : login name on remote server
# $5 : local path to odo_instances
echo '---------------------'
c1="ssh $4@$2 'bash -s' < $5/scripts/dodump.sh $1"
echo "-1-" $c1
$c1
c2="rsync -avzC --delete $4@$2:$3/$1/filestore/ $5/$1/filestore/"
echo "-2-" $c2
$c2
c3="rsync -avzC --delete $4@$2:$3/$1/dump/ $5/$1/dump/"
echo "-3-" $c3
$c3
