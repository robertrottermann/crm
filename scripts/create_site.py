#!bin/python
# -*- encoding: utf-8 -*-
import warnings
import sys
import os
import logging
from pprint import pprint

#from optparse import OptionParser
import argparse
from argparse import ArgumentParser #, _SubParsersAction
import subprocess
from subprocess import PIPE

sys.path.insert(0, os.path.split(os.path.split(os.path.realpath(__file__))[0])[0])

from config import ACT_USER, BASE_PATH, NEED_BASEINFO, FOLDERNAMES, \
    BASE_INFO_FILENAME, BASE_DEFAULTS, BASE_INFO, SITES, SITES_LOCAL, MARKER, \
    APACHE_PATH, DB_USER, DB_PASSWORD, LOGIN_INFO_FILE_TEMPLATE, REQUIREMENTS_FILE_TEMPLATE

from scripts.utilities import list_sites, check_name, create_folders, \
    update_base_info, add_site_to_sitelist, add_site_to_apache, get_config_info, \
    check_project_exists, create_new_project, module_add, construct_defaults, \
    add_aliases, check_and_create_container, checkout_sa, flatten_sites, \
    create_server_config, diff_installed_modules, install_own_modules

import scripts.vcs

from scripts.name_completer import SimpleCompleter
from scripts.update_local_db import DBUpdater

def main(opts):
    if NEED_BASEINFO or opts.reset:
        update_base_info(BASE_INFO_FILENAME, BASE_DEFAULTS)
        return

    # first handle "easy options" so we can leave again
    if opts.list_sites:
        list_sites(SITES)
        return
    # check if name is given and valid
    site_name = check_name(opts)
    if not site_name:
        print 'done..'
        return

    # resolv inheritance in sites
    flatten_sites(SITES)

    #update_default_values(default_values, for_docker=opts.docker)
    if not BASE_INFO:
        print "you should provide base info by using the -r option"
        return

    # construct defaultvalues like list of target directories
    default_values = construct_defaults(site_name, opts)

    if opts.installown or opts.updateown or opts.removeown or opts.listownmodules or opts.installodoomodules:
        install_own_modules(opts, default_values)

    if opts.listmodules:
        install_own_modules(opts, default_values, list_only=True)
        return

    if opts.showmodulediff or opts.showmodulediff_refresh:
        p = os.path.normpath('%s/.installed' % default_values['sites_home'])
        rewrite = False
        if opts.showmodulediff_refresh:
            rewrite = True
        diff_installed_modules(opts, [], p, rewrite)

    if opts.directories:
        create_folders(opts, default_values, FOLDERNAMES)
        return
    if opts.module_create:
        if not opts.module_add:
            print '--module-create is only allowed together with --module-add'
            return
    if opts.module_add:
        module_add(opts, default_values, SITES.get(site_name), opts.module_add)
        return
    if opts.add_site or opts.add_site_local:
        add_site_to_sitelist(opts, default_values)
        return
    if opts.add_apache:
        add_site_to_apache(opts, default_values)
        return
    if opts.create  or opts.simple_update or opts.create_server:
        if default_values['is_local'] and not opts.force_svn_add:
            opts.__dict__['svn_add'] = False
        data = get_config_info(default_values, opts)
        if opts.create:
            check_project_exists(default_values, opts)
            # construct list of addons read from site
            open(LOGIN_INFO_FILE_TEMPLATE % default_values['inner'], 'w').write(data % default_values)
            # overwrite requrements.txt with values from systes.py
            data = open(REQUIREMENTS_FILE_TEMPLATE % default_values['inner'], 'r').read()
            open(REQUIREMENTS_FILE_TEMPLATE % default_values['inner'], 'w').write(data % default_values)
        create_server_config(opts, default_values)

        if opts.create:
            if data:
                print '%s site created' % check_name(opts)
                if not opts.svn_add:
                    print 'site is local, not added ot the repository'
            else:
                print '%s site allredy existed' % check_name(opts)
        # make sure project was added to bash_aliases
        add_aliases(opts, default_values)
        # checkout repositories
        checkout_sa(opts)

    elif opts.create_container:
        # "-C", "--create_container",
        default_values.update(BASE_INFO)
        check_and_create_container(default_values , opts)

    elif opts.dataupdate or opts.dataupdate_docker:
        # def __init__(self, opts, default_values, site_name, foldernames=FOLDERNAMES)
        handler = DBUpdater(opts, default_values, site_name)
        handler.doUpdate(db_update = not opts.noupdatedb)

    elif opts.transferlocal or opts.transferdocker:
        handler = DBUpdater(site_name)
        handler.doTransfer(opts)

    if opts.alias:
        add_aliases(opts, default_values)

class NameAction(argparse.Action):
    # def error(self, message):
    #     display_help()
    #     exit(1)

    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(NameAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        print '%r %r %r' % (namespace, values, option_string)
        setattr(namespace, self.dest, values)

if __name__ == '__main__':
    usage = "create_system.py is tool to create and maintain local odoo developement environment\n" \
    "**************************\n" \
    "updating the local environment:\n" \
    "update_local_db.py udates the local postgres database. \nEither in a local docker container or on localhost\n\n" + \
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
    parser = ArgumentParser(usage=usage)# ArgumentParser(usage=usage)
    subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands', help='there are several sub commands')
    parser_site   = subparsers.add_parser('s', help='the option -s --site-description has the following subcommands')

    # -----------------------------------------------
    # manage sites create and update sites
    # -----------------------------------------------
    parser_manage = subparsers.add_parser('c', help='the option -m --manage-sites has the following subcommands')
    parser_manage.add_argument(
        "--add-site",
        action="store_true", dest="add_site", default=False,
        help = 'add site description to sites.py from template, also option -n --name must be set'
    )
    parser_manage.add_argument(
        "--add-site-local",
        action="store_true", dest="add_site_local", default=False,
        help = 'add site description to sites_local.py from template, also option -n --name must be set'
    )
    parser_manage.add_argument(
        "-c", "--create",
        action="store_true", dest="create", default=False,
        help = 'create new site structure in projects, also option -n --name must be set'
    )
    parser_manage.add_argument(
        "-D", "--directories",
        action="store_true", dest="directories", default=False,
        help = 'create local directories for a site. option -n must be set and valid'
    )

    # -----------------------------------------------
    # support commands
    # -----------------------------------------------
    parser_support= subparsers.add_parser('S', help='the option -S --support has the following subcommands')
    parser_support.add_argument(
        "-a", "--alias",
        action="store_true", dest="alias", default=False,
        help = 'add project site structure to aliases. create site will run this automatically'
    )
    parser_support.add_argument( # remove ?????
        "--simpleupdate",
        action="store_true", dest="simple_update", default=False,
        help = 'Just update login_info.py.in, base_setup.cfg and bin/dosetup, so we can rerun dosetup'
    )

    # -----------------------------------------------
    # manage docker
    # -----------------------------------------------
    parser_docker = subparsers.add_parser('d', help='the option -d --docker has the following subcommands')
    parser_docker.add_argument(
        "-C", "--create_container",
        action="store_true", dest="create_container", default=False,
        help = 'create a docker container, also option -n --name must be set'
    )

    # -----------------------------------------------
    # manage remote server can be localhost
    # -----------------------------------------------
    parser_remote = subparsers.add_parser('r', help='the option -r --remote has the following subcommands')
    parser_remote.add_argument(
        "--add-apache",
        action="store_true", dest="add_apache", default=False,
        help = 'add apache.conf to the local apache configuration, also option -n --name must be set'
    )
    parser_remote.add_argument(
        "-CC", "--create_server",
        action="store_true", dest="create_server", default=False,
        help = 'run create script on server -n --name must be set'
    )

#--------------------------------------------
    parser.add_argument(
        "-lo", "--listownmodules",
        action="store_true", dest="listownmodules", default=False,
        help = 'list installable modules from the sites.py sites description'
    )
    parser.add_argument(
        "-io", "--installown",
        action="store_true", dest="installown", default=False,
        help = 'install modules listed as addons'
    )
    parser.add_argument(
        "-uo", "--updateown",
        action="store", dest="updateown", default='',
        help = 'update modules listed as addons, pass a comma separated list (no spaces) or all'
    )
    parser.add_argument(
        "-ro", "--removeown",
        action="store", dest="removeown", default='',
        help = 'remove modules listed as addons, pass a comma separated list (no spaces) or all'
    )
    parser.add_argument(
        "-I", "--installodoomodules",
        action="store_true", dest="installodoomodules", default=False,
        help = 'install modules listed as odoo addons'
    )
    parser.add_argument(
        "-II",
        action="store_true", dest="showmodulediff", default=False,
        help = 'list difference on modules installed as odoo addons, keep old list'
    )
    parser.add_argument(
        "-III",
        action="store_true", dest="showmodulediff_refresh", default=False,
        help = 'list difference on modules installed as odoo addons, overwrite old list'
    )
    parser.add_argument(
        "-ls", "--list",
        action="store_true", dest="list_sites", default=False,
        help = 'list available sites'
    )
    parser.add_argument(
        "-lm", "--listmodules",
        action="store_true", dest="listmodules", default=False,
        help = 'list installable module sets like CRM ..'
    )
    parser.add_argument(
        "-n", "--name",
        action=NameAction, dest="name", default=False,
        help = 'name of the site to create'
    )
    # add second
    #parser.add_argument('sitename', nargs='?')
    parser.add_argument(
        "-N", "--norefresh",
        action="store_true", dest="norefresh", default=False,
        help = 'do not refresh local data, only update database with existing dump'
    )
    parser.add_argument(
        "-nupdb", "--noupdatedb",
        action="store_true", dest="noupdatedb", default=False,
        help = 'do not update local database, only update local data from remote site'
    )
    parser.add_argument(
        "-o", "--override-remote",
        action="store", dest="overrideremote", default=False,
        help = 'override remote settings for testing purpose'
    )
    parser.add_argument(
        "-r", "--reset",
        action="store_true", dest="reset", default=False,
        help = 'reset skeleton and projects path'
    )
    parser.add_argument(
        "-s", "--svn_add",
        action="store_true", dest="svn_add", default=True,
        help = 'Add the new project to svn (local procets will not be added), default = True'
    )
    parser.add_argument(
        "-td", "--transferdocker",
        action="store_true", dest="transferdocker", default=False,
        help = 'transfer data from master to slave using docker'
    )
    parser.add_argument(
        "-tl", "--transferlocal",
        action="store_true", dest="transferlocal", default=False,
        help = 'transfer data from master to slave using shell commands'
    )
    parser.add_argument(
        "-u", "--dataupdate",
        action="store_true", dest="dataupdate", default=False,
        help = 'update local data from remote server'
    )
    parser.add_argument(
        "-ud", "--dataupdate_docker",
        action="store_true", dest="dataupdate_docker", default=False,
        help = 'update local data from remote server into local docker'
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true", dest="verbose", default=False,
        help="be verbose")

    # ----------------------------------
    # rpc stuff
    # ----------------------------------
    parser.add_argument("-dbh", "--dbhost",
                    action="store", dest="dbhost", default='localhost',
                    help="define host default localhost")
    parser.add_argument("-rpch", "--rpchost",
                    action="store", dest="rpchost", default='localhost',
                    help="define rpchost (where odoo runs) default localhost")
    parser.add_argument("-db", "--dbname",
                    action="store", dest="dbname", default='',
                    help="define database default ''")
    parser.add_argument("-dbu", "--dbuser",
                    action="store", dest="dbuser", default=DB_USER,
                    help="define user to log into db default %s" % DB_USER)
    parser.add_argument("-rpcu", "--rpcuser",
                    action="store", dest="rpcuser", default='admin',
                    help="define user to log into odoo default admin")
    parser.add_argument("-p", "--dbpw",
                    action="store", dest="dbpw", default='admin',
                    help="define password to log into db default 'admin'")
    parser.add_argument("-P", "--rpcpw",
                    action="store", dest="rpcpw", default='admin',
                    help="define password for odoo user default 'admin'")
    parser.add_argument("-PO", "--port",
                    action="store", dest="rpcport", default=8069,
                    help="define rpc port default 8069")
    parser.add_argument("-dbp", "--dbport",
                    action="store", dest="dbport", default=5432,
                    help="define db port default 5432")

    # ----------------------------------
    # docker stuff
    # ----------------------------------
    parser.add_argument("-ddbuser", "--dockerdbuser",
                    action="store", dest="dockerdbuser", default='odoo',
                    help="user to access db in a docker, default odoo")

    parser.add_argument("-ddbpw", "--dockerdbpw",
                    action="store", dest="dockerdbpw", default='odoo',
                    help="password to access db in a docker, default odoo")


    #(opts, args) = parser.parse_args()
    opts = parser.parse_args()
    # is there a valid option?
    if not (
        opts.alias or
        opts.create_container or
        opts.create_server or
        opts.create or
        opts.directories or
        opts.list_sites or
        opts.reset or
        opts.add_apache or
        opts.add_site_local or
        opts.add_site or
        opts.module_add or
        opts.module_create or
        opts.simple_update or
        opts.dataupdate or
        opts.dataupdate_docker or
        opts.norefresh or
        opts.transferlocal or
        opts.transferdocker or
        opts.showmodulediff or
        opts.installodoomodules or
        opts.updateown or
        opts.installown or
        opts.listmodules or
        opts.listownmodules or
        opts.removeown or
        opts.showmodulediff_refresh
        ):
        print usage
        sys.exit(99)
    main(opts) #opts.noinit, opts.initonly)
