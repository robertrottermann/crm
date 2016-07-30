#!bin/python
# -*- encoding: utf-8 -*-
import warnings
import sys
import os
import logging
from pprint import pprint
from name_completer import SimpleCompleter

#from optparse import OptionParser
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

try:
    from ruamel.std.argparse import ArgumentParser, set_default_subparser
    import argparse
except ImportError:
    print '*' * 80
    print bcolors.WARNING +bcolors.FAIL + 'please run bin/pip install -r install/requirements.txt' + bcolors.ENDC
    print 'not all libraries are installed'
    print '*' * 80
    sys.exit()

#from argparse import ArgumentParser #, _SubParsersAction
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

from docker_handler import dockerHandler

import scripts.vcs

from scripts.name_completer import SimpleCompleter
from scripts.update_local_db import DBUpdater

class OptsWrapper(object):
    def __init__(self, d):
        self.__d = d
    def __getattr__(self, key):
        return hasattr(self.__d, key) and getattr(self.__d, key)
    @property
    def _o(self):
        return(self.__d)

def collect_options(opts):
    # return list of posible suboptions
    # and if a valid otion is selected
    actual = opts._o.subparser_name
    _o = opts._o._get_kwargs()
    skip = ['name', 'subparser_name', 'dockerdbpw', 'dockerdbuser']
    keys = [k[0] for k in _o if k[0] not in skip]
    is_set = [k[1] for k in _o if k[1] and (k[0] not in skip)]
    return actual, is_set, keys

def main(opts):

    if NEED_BASEINFO or opts.reset:
        update_base_info(BASE_INFO_FILENAME, BASE_DEFAULTS)
        return

    # check if name is given and valid
    site_name = check_name(opts)
    if not site_name:
        print 'done..'
        return
    print '->', site_name
    # resolv inheritance in sites
    flatten_sites(SITES)

    #update_default_values(default_values, for_docker=opts.docker)
    if not BASE_INFO:
        print "you should provide base info by using the -r option"
        return

    parsername, selected, options = collect_options(opts)
    default_values = construct_defaults(site_name, opts)
    if not selected:
        cmpl = SimpleCompleter(parsername, options)
        _o = cmpl.input_loop()
        if _o in options:
            if isinstance(opts._o.__dict__[_o], bool):
                opts._o.__dict__[_o] = True
            elif _o in ['updateown', 'removeown']:
                l = install_own_modules(opts, default_values, quiet='listownmodules')
                cmpl = SimpleCompleter(l)
                _r = cmpl.input_loop()
                if _o:
                    opts._o.__dict__[_o] = _r
            else:
                opts._o.__dict__[_o] = raw_input('value for %s:' % _o)
    # construct defaultvalues like list of target directories
    default_values = construct_defaults(site_name, opts)

    if opts.list_sites:
        list_sites(SITES)
        return

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
        if default_values['is_local']:# and not opts.force_git_add:
            opts._o.__dict__['git_add'] = False
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
                if not opts.git_add:
                    print 'site is local, not added ot the repository'
            else:
                print '%s site allredy existed' % check_name(opts)
        # make sure project was added to bash_aliases
        add_aliases(opts, default_values)
        # checkout repositories
        checkout_sa(opts)

    elif opts.docker_create_container:
        # "-C", "--create_container",
        default_values.update(BASE_INFO)
        handler = dockerHandler(opts, default_values, site_name)
        handler.check_and_create_container()

    elif opts.dataupdate or opts.dataupdate_docker:
        # def __init__(self, opts, default_values, site_name, foldernames=FOLDERNAMES)
        if opts.dataupdate:
            handler = DBUpdater(opts, default_values, site_name)
        else:
            handler = dockerHandler(opts, default_values, site_name)
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

class _HelpAction(argparse._HelpAction):

    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()

        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print("Subparser '{}'".format(choice))
                print(subparser.format_help())

        parser.exit()


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
    "sites_local.py: This file contains local site descriptions not managed by git\n" \
    "localdata.py: It contains the name and password of the local postgres user. not managed by git\n" \
    "**************************\n" \
    "\n-h for help on usage"
    parent_parser = argparse.ArgumentParser(usage=usage, add_help=False)
    parent_parser.add_argument(
        "-n", "--name",
        action="store", dest="name", default=False,
        help = 'name of the site to create'
    )
    parent_parser.add_argument(
        "-v", "--verbose",
        action="store_true", dest="verbose", default=False,
        help="be verbose")


    parser = ArgumentParser(add_help=False)# ArgumentParser(usage=usage)
    parser.add_argument('--help', action=_HelpAction, help='help for help if you need some help')  # add custom help
    parser_s = parser.add_subparsers(title='subcommands', dest="subparser_name")
    #parser_site   = parser_s.add_parser('s', help='the option -s --site-description has the following subcommands', parents=[parent_parser])

    # -----------------------------------------------
    # manage sites create and update sites
    # -----------------------------------------------
    #http://stackoverflow.com/questions/10448200/how-to-parse-multiple-sub-commands-using-python-argparse
    #parser_site_s = parser_site.add_subparsers(title='manage sites', dest="site_creation_commands")
    parser_manage = parser_s.add_parser(
        'create',
        help='create --manage-sites has the following subcommands',
        #aliases=['c'],
        parents=[parent_parser],
        prog='PROG',
        usage='%(prog)s [options]')
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
    parser_manage.add_argument(
        "-lo", "--listownmodules",
        action="store_true", dest="listownmodules", default=False,
        help = 'list installable modules from the sites.py sites description'
    )
    parser_manage.add_argument(
        "-io", "--installown",
        action="store_true", dest="installown", default=False,
        help = 'install modules listed as addons'
    )
    parser_manage.add_argument(
        "-uo", "--updateown",
        action="store", dest="updateown", default='',
        help = 'update modules listed as addons, pass a comma separated list (no spaces) or all'
    )
    parser_manage.add_argument(
        "-ro", "--removeown",
        action="store", dest="removeown", default='',
        help = 'remove modules listed as addons, pass a comma separated list (no spaces) or all'
    )
    parser_manage.add_argument(
        "-I", "--installodoomodules",
        action="store_true", dest="installodoomodules", default=False,
        help = 'install modules listed as odoo addons'
    )
    parser_manage.add_argument(
        "-ls", "--list",
        action="store_true", dest="list_sites", default=False,
        help = 'list available sites'
    )
    parser_manage.add_argument(
        "-lm", "--listmodules",
        action="store_true", dest="listmodules", default=False,
        help = 'list installable module sets like CRM ..'
    )
    parser_manage.add_argument(
        "-N", "--norefresh",
        action="store_true", dest="norefresh", default=False,
        help = 'do not refresh local data, only update database with existing dump'
    )
    parser_manage.add_argument(
        "-nupdb", "--noupdatedb",
        action="store_true", dest="noupdatedb", default=False,
        help = 'do not update local database, only update local data from remote site'
    )
    parser_manage.add_argument(
        "-o", "--override-remote",
        action="store", dest="overrideremote", default=False,
        help = 'override remote settings for testing purpose'
    )
    parser_manage.add_argument(
        "-u", "--dataupdate",
        action="store_true", dest="dataupdate", default=False,
        help = 'update local data from remote server'
    )

    # -----------------------------------------------
    # support commands
    # -----------------------------------------------
    #parser_manage_s = parser_manage.add_subparsers(title='manage sites', dest="site_manage_commands")
    parser_support= parser_s.add_parser('support', help='the option -sites --support has the following subcommands', parents=[parent_parser])
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
    parser_support.add_argument(
        "-II",
        action="store_true", dest="showmodulediff", default=False,
        help = 'list difference on modules installed as odoo addons, keep old list'
    )
    parser_support.add_argument(
        "-III",
        action="store_true", dest="showmodulediff_refresh", default=False,
        help = 'list difference on modules installed as odoo addons, overwrite old list'
    )
    parser_support.add_argument(
        "-r", "--reset",
        action="store_true", dest="reset", default=False,
        help = 'reset skeleton and projects path'
    )

    # -----------------------------------------------
    # manage docker
    # -----------------------------------------------
    #parser_support_s = parser_support.add_subparsers(title='docker commands', dest="docker_commands")
    parser_docker = parser_s.add_parser(
        'docker', 
        #aliases=['d'],        
        help='the option --docker has the following subcommands', 
        parents=[parent_parser])
    parser_docker.add_argument(
        "-dc", "--create_container",
        action="store_true", dest="docker_create_container", default=False,
        help = 'create a docker container, also option -n --name must be set'
    )
    parser_docker.add_argument("-ddbuser", "--dockerdbuser",
                        action="store", dest="dockerdbuser", default='odoo',
                        help="user to access db in a docker, default odoo")

    parser_docker.add_argument("-ddbpw", "--dockerdbpw",
                        action="store", dest="dockerdbpw", default='odoo',
                        help="password to access db in a docker, default odoo")

    parser_docker.add_argument(
        "-dtd", "--transferdocker",
        action="store_true", dest="transferdocker", default=False,
        help = 'transfer data from master to slave using docker'
    )
    parser_docker.add_argument(
        "-dud", "--dataupdate_docker",
        action="store_true", dest="dataupdate_docker", default=False,
        help = 'update local data from remote server into local docker'
    )

    # -----------------------------------------------
    # manage remote server (can be localhost)
    # -----------------------------------------------
    #parser_docker_s = parser_docker.add_subparsers(title='remote commands', dest="remote_commands")
    parser_remote = parser_s.add_parser(
        'remote', 
        #aliases=['r'],    
        help='the option -r --remote has the following subcommands', 
        parents=[parent_parser])
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
    parser_remote.add_argument(
        "-tl", "--transferlocal",
        action="store_true", dest="transferlocal", default=False,
        help = 'transfer data from master to slave using shell commands'
    )
    # -----------------------------------------------
    # manage rpc stuff
    # -----------------------------------------------
    #parser_remote_s = parser_remote.add_subparsers(title='remote commands', dest="rpc_commands")
    parser_rpc = parser_s.add_parser('rpc', help='the option rpc has the following subcommands', parents=[parent_parser])
    parser_rpc.add_argument("-dbh", "--dbhost",
                    action="store", dest="dbhost", default='localhost',
                    help="define host default localhost")
    parser_rpc.add_argument("-rpch", "--rpchost",
                    action="store", dest="rpchost", default='localhost',
                    help="define rpchost (where odoo runs) default localhost")
    parser_rpc.add_argument("-db", "--dbname",
                    action="store", dest="dbname", default='',
                    help="define database default ''")
    parser_rpc.add_argument("-dbu", "--dbuser",
                    action="store", dest="dbuser", default=DB_USER,
                    help="define user to log into db default %s" % DB_USER)
    parser_rpc.add_argument("-rpcu", "--rpcuser",
                    action="store", dest="rpcuser", default='admin',
                    help="define user to log into odoo default admin")
    parser_rpc.add_argument("-p", "--dbpw",
                    action="store", dest="dbpw", default='admin',
                    help="define password to log into db default 'admin'")
    parser_rpc.add_argument("-P", "--rpcpw",
                    action="store", dest="rpcpw", default='admin',
                    help="define password for odoo user default 'admin'")
    parser_rpc.add_argument("-PO", "--port",
                    action="store", dest="rpcport", default=8069,
                    help="define rpc port default 8069")
    parser_rpc.add_argument("-dbp", "--dbport",
                    action="store", dest="dbport", default=5432,
                    help="define db port default 5432")

    #(opts, args) = parser.parse_args()
    parser.set_default_subparser('create')
    args, unknownargs = parser.parse_known_args()
    opts = OptsWrapper(args)
    if not opts.name and unknownargs:
        opts._o.__dict__['name'] = unknownargs[0]

    # is there a valid option?
    main(opts) #opts.noinit, opts.initonly)
