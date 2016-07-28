#!/bin/sh
echo ssh $4@$2 'bash -s' < scripts/dodump.sh $1
ssh $4@$2 'bash -s' < scripts/dodump.sh $1
echo rsync -C $4@$2:$1.dmp sql_dumps/$1.dmp
rsync -C $4@$2:$1.dmp sql_dumps/$1.dmp
