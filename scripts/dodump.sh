#!/bin/sh
# dodump.sh dumps a site's database into its folder
# the folder is /root/odoo_instances/$1/dump where $1 represents the site's name
# dodump creates a temporary docker container that dumps a servers database
# it is called by updatedb.sh and executed on the remote computer
sudo docker run -v /root/odoo_instances:/mnt/sites  --rm=true --link db:db  dbdumper -d $1
