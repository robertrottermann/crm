#!bin/python
# -*- encoding: utf-8 -*-
import warnings
import sys
import os
import logging
from optparse import OptionParser
import subprocess
from subprocess import PIPE
sys.path.insert(0, '.')

from config import FOLDERNAMES

"""
robert@mozart:~/projects/redproducts/redproducts$ psql -U robert -d postgres
psql (9.4.4)
Type "help" for help.

postgres=# drop database redproducts;
DROP DATABASE
postgres=# create database redproducts;
CREATE DATABASE

"""
SITES_HOME =  os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
sys.path.insert(0, SITES_HOME)
# we import SITES here, so that it only contains non local sites
from sites import SITES
from utilities import get_remote_server_info

def which(file):
    for path in os.environ["PATH"].split(os.pathsep):
        if os.path.exists(os.path.join(path, file)):
                return os.path.join(path, file)

    return None

# #1676  rsync -z --delete -av root@144.76.184.20:/opt/odoo/.local/share/Odoo/filestore/redproducts/ /home/robert/projects/redproducts/redproducts/parts/filestore/redproducts/
#     "breitschtraeff" : {
#         'servename' : '144.76.184.20',
#         'remote_path' : '/root/odoo_instances',
#         'remote_user' : 'root'
#     },

class DBUpdater(object):
    """
    class to do update the loacal database
    """
    dpath = ''
    def __init__(self, opts, default_values, site_name, foldernames=FOLDERNAMES):
        site_names = []
        if site_name == 'all':
            site_names = SITES.keys()
        else:
            if site_name.endswith('/'):
                site_name = site_name[:-1]

            site_names = [site_name]
            if not site_names:
                print '-------------------------------------------------------'
                print 'invalid site name %s' % site_name
                print '-------------------------------------------------------'
                return
        self.opts = opts
        self.default_values = default_values
        self.site_names = site_names
        self.sites_home = default_values['sites_home']

    # ------------------------------------
    # get_value_from_config
    # gets a value from etc/open_erp.conf
    # ------------------------------------
    def get_value_from_config(self, path, key=''):
        res = {}
        for l in open(path):
            if l and l.find('=') > -1:
                parts = l.split('=', 1)
                res[parts[0].strip()] = parts[1].strip()
        if key:
            return res.get(key)
        else:
            return res

    # ------------------------------------
    # get_instance_list
    # checks all subdirectories whether
    # they provide an etc/open_erp.conf
    # if yes, it is considered to be an
    # openerp site
    # a dict of {'sitename' : dbname, ..}
    #   is returned
    # ------------------------------------
    def get_instance_list(self):
        opts = self.opts
        home = self.sites_home
        dirs = [d for d in os.listdir(home) if os.path.isdir('%s/%s' % (home, d))]
        result = {}
        for d in dirs:
            p = '%s/%s/etc/openerp-server.conf' % (home, d)
            if os.path.exists(p):
                db = self.get_value_from_config(p, 'db_name')
                result[d] = db
                if opts.verbose:
                    print d, 'db:', get_value_from_config(p, 'db_name')
        return result

    def create_folders(self, path_name, quiet=True):
        errors = False
        if not path_name:
            print 'site name not provided'
            return
        p = os.path.normpath('%s/../%s' % (os.path.dirname(os.path.abspath(__file__)), path_name))
        for pn in [''] + self.foldernames: #FOLDERNAMES:
            try:
                pp = '%s/%s' % (p, pn)
                os.mkdir(pp)
            except:
                errors = True
                if not quiet:
                    print 'could not create %s' % pp
        if not quiet:
            if errors:
                print 'not all directories could be created'
            else:
                print 'directories for %s created' % check_name(opts)

    def doUpdate(self, db_update=True, norefresh=None, names=[]):
        opts = self.opts
        if not names:
            names = self.site_names
        if norefresh is None:
            norefresh = opts.norefresh
        for db_name in names:
            db_data = SITES[db_name]
            # we have to get info about the remote server indirectly
            # as it could be overridden by overrideremote
            remote_path = db_data.get('remote_server', {'remote_path' : '/root/odoo_instances'})['remote_path']

            server_dic = get_remote_server_info(opts)
            remote_url = server_dic.get('remote_url')
            remote_user = server_dic.get('remote_user')
            remote_data_dir = server_dic.get('remote_path')
            # pg_password is on local host. even when run remotely
            pg_password = db_data.get('pg_password')
            try:
                if opts.backup:
                    # we want to make sure the local directories exist
                    self.create_folders(db_name)
            except AttributeError:
                pass

            dpath = '%s/%s/dump/%s.dmp' % (self.sites_home, db_name, db_name)
            if not norefresh:
                os.system('%s/scripts/updatedb.sh %s %s %s %s %s' % (self.sites_home, db_name, remote_url, remote_data_dir, remote_user, self.sites_home))
                # if remote user is not root we first have to copy things where we can access it
                if remote_user != 'root':
                    # this calls the remote site_syncer.py script
                    # it copy needed files to the users home and changes ownership
                    os.system('%s/scripts/updatedb_remote.sh %s %s %s %s %s' % (self.sites_home, db_name, remote_url, remote_data_dir, remote_user, remote_path))
                # rsync the remote files to the local directories
                os.system('%s/scripts/rsync_remote_local.sh %s %s %s %s' % (self.sites_home, db_name, remote_url, remote_data_dir, remote_user))
                if not os.path.exists(dpath):
                    print '-------------------------------------------------------'
                    print '%s not found' % dpath
                    print '-------------------------------------------------------'
                    continue
                try:
                    if opts.backup:
                        # no need to update database
                        continue
                except AttributeError:
                    pass
            if db_update:
                if opts.dataupdate_docker:
                    # we need to learn what ip address the local docker db is using
                    from docker import Client
                    cli = Client(base_url='unix://var/run/docker.sock')
                    remote_url = cli.containers(filters = {'name' : 'db'})[0][u'NetworkSettings'][u'Networks']['bridge']['IPAddress']
                    remote_user = opts.dockerdbuser
                    remote_data_dir = self.sites_home
                    pg_password = opts.dockerdbpw
                    pw = pg_password
                    user = remote_user
                else:
                    # what is the local user that is allowed to update the local db
                    from localdata import DB_USER, DB_PASSWORD
                    pw   = DB_PASSWORD
                    user = DB_USER
                shell = False
                # mac needs absolute path to psql
                where = os.path.split(which('psql'))[0]
                wd = which('docker')
                if wd:
                    whered = os.path.split(wd)[0]
                else:
                    whered = ''
                if whered:
                    cmd_lines_docker = [
                        ['%s/docker run -v %s:/mnt/sites --rm=true --link db:db -it dbdumper -r %s' % (whered, self.sites_home, db_name)]
                    ]
                else:
                    cmd_lines_docker = [
                        ['docker run -v %s:/mnt/sites --rm=true --link db:db -it dbdumper -r %s' % (self.sites_home, db_name)]
                    ]
                cmd_lines_no_docker = [
                    # delete the local database(s)
                    ['%s/psql' % where, '-U', user, '-d', 'postgres',  '-c', "drop database IF EXISTS %s;" % db_name],
                    # create database again
                    ['%s/psql' % where, '-U', user, '-d', 'postgres',  '-c', "create database %s;" % db_name],
                    # do the actual reading of the database
                    # the database will have thae same name as on the remote server
                    ['%s/pg_restore' % where, '-O', '-U', user, '-d', db_name, dpath],
                    # set standard password
                    ['%s/psql' % where, '-U', user, '-d', db_name,  '-c', "update res_users set password='admin' where login='admin';"],
                ]
                cmd_lines = [
                ]

                if opts.dataupdate_docker or opts.transferdocker:
                    cmd_lines = cmd_lines_docker + cmd_lines
                    shell = True
                else:
                    cmd_lines = cmd_lines_no_docker + cmd_lines
                self.run_commands(cmd_lines, shell=shell)

    def doTransfer(self):
        # transfer data from on docker acount to an other
        # the following steps have to be executed
        # - dump the source
        # - copy the source to the target. changing the folder in target
        # - stoping the target container
        # - restoring the source dump into target
        # - restarting target container

        # the transfer always is done on localhost
        opts = self.opts
        for site_name in self.site_names:
            slave_db_data = SITES[site_name]
            # we have to get info about the remote server indirectly
            # as it could be overridden by overrideremote
            server_dic = get_remote_server_info(opts)
            if not server_dic:
                return
            if not site_name in self.get_instance_list():
                print '*' * 80
                print 'site %s does not exist or is not initialized' % site_name
                print 'run bin/c.sh -D %s' % site_name
                if len(self.site_names) > 1:
                    continue
                return
            remote_url = 'localhost' #server_dic.get('remote_url')
            remote_user = server_dic.get('remote_user')
            remote_data_dir = server_dic.get('remote_path')
            # pg_password is on local host. even when run remotely
            pg_password = slave_db_data.get('pg_password')
            dpath = '%s/%s/dump/%s.dmp' % (self.sites_home, site_name, site_name)

            # get info about main site
            if opts.transferdocker:
                docker_info = slave_db_data.get('docker')
                if not docker_info or not docker_info.get('container_name'):
                    print '*' * 80
                    print 'no docker info found for %s, or container_name not set' % site_name
                    if len(self.site_names) > 1:
                        continue
                    return
            slave_info = slave_db_data.get('slave_info')
            if not slave_info:
                print '*' * 80
                print 'no slave info found for %s' % site_name
                if len(self.site_names) > 1:
                    continue
                return
            master_name = slave_info.get('master_site')
            if not master_name in self.get_instance_list():
                print '*' * 80
                print 'master_site %s does not exist or is not initialized' % master_name
                print 'run bin/c.sh -D %s' % master_name
                if len(self.site_names) > 1:
                    continue
                return
            if not master_name:
                print '*' * 80
                print 'master_site not provided for %s' % site_name
                if len(self.site_names) > 1:
                    continue
                return
            master_db_data = SITES[master_name]
            master_server_dic = get_remote_server_info(opts, master_name)
            master_remote_url = 'localhost' #server_dic.get('remote_url')
            master_remote_user = server_dic.get('remote_user')
            master_remote_data_dir = server_dic.get('remote_path')
            # update local master file, but not local database
            self.doUpdate(db_update=False, names=[master_name])
            # rsync -avzC --delete /home/robert/odoo_instances/afbs/filestore/afbs/ /home/robert/odoo_instances/afbstest/filestore/afbstest/
            ddiC = {
                'base_path' : self.sites_home,
                'master_name' : master_name,
                'master_db_name' : master_db_data['db_name'],
                'slave_name' : site_name,
                'slave_db_name' : slave_db_data['db_name']
            }
            # make sure directory for the rsync target exist
            rsync_target = '%(base_path)s/%(slave_name)s/filestore/%(slave_name)s/' % ddiC
            if not os.path.exists(rsync_target):
                os.makedirs(rsync_target)
            cmd_lines = [
                'rsync -avzC --delete %(base_path)s/%(master_name)s/dump/%(master_name)s.dmp  %(base_path)s/%(slave_name)s/dump/%(slave_name)s.dmp' % ddiC,
                'rsync -avzC --delete %(base_path)s/%(master_name)s/filestore/%(master_db_name)s/  %(base_path)s/%(slave_name)s/filestore/%(slave_db_name)s/' % ddiC,
            ]
            # now we have to decide whether docker needs to be used
            if opts.transferdocker:
                # stop local docker
                stopdocker = 'docker stop %s' % docker_info.get('container_name')
                cmd_lines += [stopdocker]
            # execute transfer
            self.run_commands(cmd_lines)
            # update database
            self.doUpdate(names=[site_name], norefresh=True)
            if opts.transferdocker:
                # restart local docker
                startdocker = 'docker restart %s' %docker_info.get('container_name')
                cmd_lines += [startdocker]
                self.run_commands(cmd_lines)

    def run_commands(self, cmd_lines, shell=True):
        from localdata import DB_USER, DB_PASSWORD
        opts = self.opts
        pw   = DB_PASSWORD
        user = DB_USER
        counter = 0
        for cmd_line in cmd_lines:
            counter +=1
            if opts.verbose:
                print 'counter:', counter
            if not cmd_line:
                continue
            print '-' * 80
            print cmd_line
            p = subprocess.Popen(
                cmd_line,
                stdout=PIPE,
                env=dict(os.environ, PGPASSWORD=pw,  PATH='/usr/bin'),
                shell=shell)
            if opts.verbose:
                print p.communicate()
            else:
                p.communicate()

def main():
    usage = "update_local_db.py udates the local postgres database. \nEither in a local docker container or on localhost\n\n" + \
    "First the remote data is read by running a temporary docker container on the remote site\n" \
    "that dumps the remote database into the sites dump directory\n" \
    "then this directory together with the sites data directory is copied to local host using rsync\n\n" \
    "**************************\n" \
    "the following files are read:\n" \
    "sites.py: This file contains a set of site descriptions\n" \
    "sites_local.py: This file contains local site descriptions not managed by svn\n" \
    "localdata.py: It contains the name and password of the local postgres user. not managed by svn\n" \
    "**************************\n" \
    "\n-h for help on usage"
    parser = OptionParser(usage=usage)

    parser.add_option("-b", "--backup",
                    action="store_true", dest="backup", default=False,
                    help="create backup. This only copies remote data and files. It will create folders if necessary")

    parser.add_option("-d", "--docker",
                    action="store_true", dest="docker", default=False,
                    help="use docker to run local database, default false")

    parser.add_option("-l", "--list",
                    action="store_true", dest="list_sites", default=False,
                    help="list existing sites")

    parser.add_option("-n", "--name",
                    action="store", dest="name", default='',
                    help="reload remote server-data into local database, use all to reload all or comma separated list of sites\nthis is done by droping the database and recostructing it")

    parser.add_option("-N", "--norefresh",
            action="store_true", dest="norefresh", default=False,
            help = 'do not refresh local data, only update database with existing dump')

    parser.add_option("-v", "--verbose",
                    action="store_true", dest="verbose", default=False,
                    help="be verbose")

    (opts, args) = parser.parse_args()

    if opts.list_sites:
        for n in SITES.keys():
            print n
    elif opts.name:
        handler = DBUpdater(opts.name)
        handler.doUpdate(opts)
    else:
        print usage



if __name__ == '__main__':
    main()
