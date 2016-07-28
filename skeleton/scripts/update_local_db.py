#!bin/python
# -*- encoding: utf-8 -*-
import warnings
import sys
import os
import logging
from optparse import OptionParser
import subprocess
from subprocess import PIPE

"""
robert@mozart:~/projects/redproducts/redproducts$ psql -U robert -d postgres
psql (9.4.4)
Type "help" for help.

postgres=# drop database redproducts;
DROP DATABASE
postgres=# create database redproducts;
CREATE DATABASE

"""


PROJECT_HOME =  os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
CFGNAME = 'openerp.cfg'
DATAPATH = 'sql_dumps'

def get_config_data():
    result = {}
    dpath = '%s/etc/%s' % (PROJECT_HOME, CFGNAME)
    with open(dpath, 'r') as f:
        for line in f:
            if (not line) or (not (line.find('=') > -1)):
                continue
            
            k, v = [e.strip() for e in line.split('=')]
            result[k] = v
    return result

def which(file):
    for path in os.environ["PATH"].split(os.pathsep):
        if os.path.exists(os.path.join(path, file)):
                return os.path.join(path, file)

    return None

#1676  rsync -z --delete -av root@144.76.184.20:/opt/odoo/.local/share/Odoo/filestore/redproducts/ /home/robert/projects/redproducts/redproducts/parts/filestore/redproducts/
class DBUpdater(object):
    dpath = ''
    def __init__(self, db_name=''):
        self.config_data = get_config_data()
        if not db_name:
            db_name = self.config_data.get('db_name')
            if not db_name:
                print '-------------------------------------------------------'
                print 'no dbname defined'
                print '-------------------------------------------------------'
                return
        self.db_remote = self.config_data.get('remote_database')
        self.remote_url = self.config_data.get('remote_url')
        self.pg_password = self.config_data.get('pg_password')
        self.remote_user = self.config_data.get('remote_user')
        self.data_dir = self.config_data.get('data_dir')
        self.remote_data_dir = self.config_data.get('remote_data_dir')
        
        os.system('scripts/updatedb.sh %s %s %s %s' % (self.db_remote, self.remote_url, self.pg_password, self.remote_user))
        self.db_name = db_name
        dpath = '%s/%s/%s.dmp' % (PROJECT_HOME, DATAPATH, self.db_remote)
        if os.path.exists(dpath):
            self.dpath = dpath
        else:
            print '-------------------------------------------------------'
            print '%s not found' % dpath
            print '-------------------------------------------------------'
        
    
    def doUpdate(self):
        if not self.dpath:
            return
        pw   = self.config_data.get('db_password')
        user = self.config_data.get('db_user')
        # mac needs absolute path to psql
        where = os.path.split(which('psql'))[0]
        if self.db_remote == self.db_name:
            rename_db = []
        else:
            # rename database to local name
            rename_db =  ['%s/psql' % where, '-U', user, '-d', 'postgres',  '-c', "alter database %s rename to %s;" % (self.db_remote, self.db_name)]
        cmd_lines = [
            # delete the local database(s)
            ['%s/psql' % where, '-U', user, '-d', 'postgres',  '-c', "drop database IF EXISTS %s;" % self.db_name],
            ['%s/psql' % where, '-U', user, '-d', 'postgres',  '-c', "drop database IF EXISTS %s;" % self.db_remote],
            # do the actual reading of the database
            # the database will have thae same name as on the remote server
            ['%s/pg_restore' % where, '-O', '-C', '-U', user, '-d', 'postgres', self.dpath],
            # rename database to local name
            rename_db,
            # set standard password
            ['%s/psql' % where, '-U', user, '-d', self.db_name,  '-c', "update res_users set password='admin' where login='admin';"],
            # now we rsync the filestorace dirs
            ['rsync', 
                '-z', 
                '--delete', 
                '-av', 
                '%s/' % os.path.normpath('%s@%s:%s/filestore/%s' % (self.remote_user,self.remote_url,self.remote_data_dir, self.db_remote)), 
                '%s/' % os.path.normpath('%s/filestore/%s' % (self.data_dir, self.db_name)),
            ],
        ]
        
        #cmd_line = ['PGPASSWORD=%s' % pw, 'psql', '-U', user, '-d', self.db_name, '< %s' % self.dpath]
        #print cmd_line
        #p = subprocess.Popen(cmd_line, shell=True, stdout=PIPE)
        #print p.communicate()
        # create filestorage directory
        try:
            # os.makedirs(self.data_dir)
            os.makedirs(os.path.normpath('%s/filestore' % self.data_dir))
        except OSError as exc:  # Python >2.5
            pass
        for cmd_line in cmd_lines:
            if not cmd_line:
                continue
            print ' '.join(cmd_line)
            p = subprocess.Popen(cmd_line, stdout=PIPE, env=dict(os.environ, PGPASSWORD=pw,  PATH='/usr/bin'))
            p.communicate()
            #os.system(' '.join(cmd_line))
        
handler = DBUpdater()
handler.doUpdate()
