#!/bin/sh
# updatedb.sh executes the script dodump_remote on a remote server
# it runs site_syncer on the remote server. this script runs as root
# and rsyncs the sites files to a place from where we can copy it
# parameters:
# $1 : site name
# $2 : server url
# $3 : remote_path like /root/odoo_instances
# $4 : login name on remote server
# $5 : path to instances home on the remote server (/root/odoo_sites)
echo ssh $4@$2 'bash -s' < scripts/dodump_remote.sh $s $2 $3 $4 $5
ssh $4@$2 'bash -s' < scripts/dodump_remote.sh $1 $2 $3 $4 $5
