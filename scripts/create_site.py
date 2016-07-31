#!bin/python
# -*- encoding: utf-8 -*-
import warnings
import sys
import os
import logging
from pprint import pprint
from name_completer import SimpleCompleter

"""
to do:
------
ODOO_SERVER_DATA config variable
dumper.py should make use of this variable.
have an alias for each remote server in local_data.py
that allows to test things locally

re-moddel sites in sites.py to have a mails structure
add a version number to sites.py
make an update script that applies changes to sites.py according to its
actual version
create an option that configures the mail servers on the target server

install own needs either a string with comma separated options or all
"""

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
    create_server_config, diff_installed_modules, install_own_modules, \
    name_neded

# scripts.vcs handles git stuff
import scripts.vcs
# name_completer handles completion of otion lists
from scripts.name_completer import SimpleCompleter
# DBUpdater handles updating of postgres daatabases and the copying of the filestore
from scripts.update_local_db import DBUpdater
# dockerHandler handles getting and updating of date that resides within containers
from docker_handler import dockerHandler

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
    skip = ['name', 'subparser_name', 'dockerdbpw', 'dockerdbuser', 'dbhost', 'dbpw', 'dbuser', 'rpchost', 'rpcport', 'rpcuser', 'rpcpw']
    keys = [k[0] for k in _o if k[0] not in skip]
    is_set = [k[1] for k in _o if k[1] and (k[0] not in skip)]
    return actual, is_set, keys

def main(opts):

    # reset
    # -----
    # when we start the first time or want to reset the stored config
    # these values are writen to $SITES_HOME/config/base_info.py
    # - project path: the path to the folder, where the projects are added to
    # - docker_path_map : mapping applied to the paths assigned to the
    #   docker volumes names when you run docker as a non root user.
    #   This helps to keep the same file structure on the remote and local
    #   server.
    # - serer data path: where server data is stored in a folder structure
    #   for each server
    if NEED_BASEINFO or opts.reset:
        update_base_info(BASE_INFO_FILENAME, BASE_DEFAULTS)
        return

    # check if name is given and valid
    site_name = check_name(opts, no_completion = True, must_match=True)

    # resolve inheritance within sites
    flatten_sites(SITES)

    # should never happen ..
    if not BASE_INFO:
        print "you should provide base info by using the -r option"
        return

    # collect info on what parser and what options are selected
    parsername, selected, options = collect_options(opts)

    # default_values contains all we know about the sities, their physical
    # location, our permission how we can connect them ..
    default_values = construct_defaults(site_name, opts)

    # the user can start using different paths
    # - without selecting anything:
    #   the create parser will be preselected
    # - without providing a full site name
    #   a site name will be asked for. if an invalid or partial name
    #   has bee provided, it will be used as default
    # - with a set of valid options
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

    # now we can really check whether name is given and valid
    site_name = check_name(opts)
    # if we have an option that nees a name ..
    if name_neded(opts) and not site_name:
        print 'done..'
        return

    # construct default values like list of target directories
    default_values = construct_defaults(site_name, opts)

    # --------------------------------------------------------
    # simple options from which we return after completion
    # therefore only one of them can be sensibly selecte
    # --------------------------------------------------------

    # list_sites
    # ----------
    # list_sites lists all existing sites both from global and local sites
    if opts.list_sites:
        list_sites(SITES)
        return

    # showmodulediff and showmodulediff_refresh
    # -----------------------------------------
    # showmodulediff and showmodulediff_refresh are auxiliary otions that are
    # only needed to create the install block
    if opts.showmodulediff or opts.showmodulediff_refresh:
        p = os.path.normpath('%s/.installed' % default_values['sites_home'])
        rewrite = False
        if opts.showmodulediff_refresh:
            rewrite = True
        diff_installed_modules(opts, [], p, rewrite)

    # directories
    # -----------
    # directories creates the needed directory scruture in $ODOO_SERVER_DATA
    #
    # this option is automaticall executed for all modules that rely on
    # the datastructure to exist.
    if opts.directories:
        create_folders(opts, default_values, FOLDERNAMES)
        return

    # add_site
    # --------
    # add_site adds a site description to the sites.py file
    # add_site_local adds a site description to the sites_local.py file
    if opts.add_site or opts.add_site_local:
        add_site_to_sitelist(opts, default_values)
        return

    # add_apache
    # ----------
    # add_apache adds a virtual host to the appache configuration
    # it is meant to run as user root on the remote server
    # if it is run locally (without root permission) it only prints the
    # content it would have written to the console
    #
    # the create the virtual host stanza add_apache collects info from sites.py
    # for $SITENAME. it uses the data found with the key "apache"
    # it collects these data:
    # - vservername: the name/url to acces the virtual server like: www.redcor.ch
    # - protokols: list of protokols to use like ['http', 'https']
    # - vserveraliases: list of alias name like ['redcor.ch']
    # to calculate the port under which the server runs the key
    # docker is used.
    # - odoo_port: port the docker container exposes to acess its odoo server
    if opts.add_apache:
        add_site_to_apache(opts, default_values)
        return

    # list_modules
    # -----------
    # list_modules list defined odoo install blocks
    # each install block contains from a list of addons that and odoo module
    # like CRM installs
    if opts.listmodules:
        install_own_modules(opts, default_values, list_only=True)
        return

    # listownmodules
    # --------------
    # list the modules that are declared within the selected site
    # installown install all modules declared in the selected site
    # updateown updates one or all modules declared in the selected site
    # removeown removes one or all modules declared in the selected site
    if opts.listownmodules or opts.installodoomodules:
        install_own_modules(opts, default_values)
        return

    # alias
    # -----
    # adds a number of aliases to local ~/.bash_aliases
    # these aliases are:
    # $SITENAME cd $PROJECT_HOME/$SITENAME/$SITENAME
    # $SITENAMEhome cd $PROJECT_HOME/$SITENAME
    # $SITENAMEa cd $PROJECT_HOME/$SITENAME/$SITENAME/$SITENAME_addons
    #
    # this option is run automatically when a site is built
    if opts.alias:
        add_aliases(opts, default_values)
        return

    # --------------------------------------------------------
    # stackable options from which we DO NOT return after completion
    # any number of the can be selected, oder of execution is not defined
    # --------------------------------------------------------

    # installown or updateown or removeown
    # ------------------------------------
    # installown install all modules declared in the selected site
    # updateown updates one or all modules declared in the selected site
    # removeown removes one or all modules declared in the selected site
    #
    # to be able to execute do this, the target server has to be running.
    # this server is accessed uding odoo's rpc_api.
    # to do so, info on user, that should access the running server needs
    # to be collected. the following values
    # read from either the config data or can be set using command line options.
    # --- database ---
    # - db_user : the user to access the servers database
    #   to check what modules are allready installed the servers database
    #   has to be accessed.
    #   option: "-dbu", "--dbuser".
    #   default: logged in user
    # - db_password
    #   option: "-p", "--dbpw".
    #   default: admin
    # - dbhost: the host on which the database is running
    #   option: "-dbh", "--dbhost"
    #   default: localhost.
    # --- user accessing the running odoo server ---
    # - rpcuser: the login user to access the odoo server
    #   option: "-rpcu", "--rpcuser"
    #   default: admin.
    # - rpcpw: the login password to access the odoo server
    #   option: "-P", "--rpcpw"
    #   default: admin.
    # - rpcport: the the odoo server is running at
    #   option: "-PO", "--port"
    #   default: 8069.

    if opts.installown or opts.updateown or opts.removeown:
        install_own_modules(opts, default_values)

    # create
    # ------
    # builds or updates a server structure
    # to do so, it does a number of steps
    #   - creates the needed folders in $ODOO_SERVER_DATA
    #   - creates a build structure in $PROJECT_HOME/$SITENAME/$SITENAME
    #     where $PROJECT_HOME is read from the config file.
    #   - copies and sets up all files from skeleton directory to the build structure
    #     this is done executing create_new_project and do_copy
    #   - builds a virtualenv environment in the build structure
    #   - prepares to builds an odoo server within the build structure by
    #     execution  bin/buildout within the build structure.
    #     Within this buildout environment odoos module path will be set
    #     that it points to the usual odoo directories within the build substructure
    #     and also to the directories within odoo_instances as dictated by the
    #     various modules installed from interpreting the site declaration
    #     in sites.py
    #   - add a "private" addons folder within the build structure called
    #     $SITENAME_addons. This folder is also added to odoos addon path.
    #   - set the data_dir to point to $ODOO_SERVER_DATA/$SITENAME/filestorage
    #
    # simple_update
    # -------------
    # it is ment to update a local site.
    # it is not in a well defined state just now
    #
    # create_server
    # -------------
    # it is similar to create but is meant to be run on the remote server
    # it assumes that the remote odoo instance runs in a docker container.
    # it also does create the needed structure and builds the odoo addons path
    # but does not build the odoo server bouildout environment in
    # $PROJECT_HOME/$SITENAME/$SITENAME.
    # it executes these steps:
    #   - create folder structure in $ODOO_SERVER_DATA
    #   - create a config file in $ODOO_SERVER_DATA/etc/openerp.cfg
    #   - set the data_dir to point to $ODOO_SERVER_DATA/$SITENAME/filestorage
    #   - set the log file to $ODOO_SERVER_DATA/$SITENAME/log/odoo.log

    if opts.create  or opts.simple_update or opts.create_server:
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
            else:
                print '%s site allredy existed' % check_name(opts)
        # make sure project was added to bash_aliases
        add_aliases(opts, default_values)
        # checkout repositories
        checkout_sa(opts)

    # docker_create_container
    # -----------------------
    # it creates and starts a docker container
    # the created container collects info from sites.py for $SITENAME
    # it uses the data found with the key "docker"
    # it collects these data:
    # - container_name: name of the container to create.
    #   must be unique for each remote server
    # - odoo_image_version: name of the docker image used to build
    #   the container
    # - odoo_port: port on which to the running odoo server within the
    #   container can be reached. must be unique for each remote server
    if opts.docker_create_container:
        # "-C", "--create_container",
        default_values.update(BASE_INFO)
        handler = dockerHandler(opts, default_values, site_name)
        handler.check_and_create_container()

    # dataupdate or dataupdate_docker
    # -------------------------------
    # these options are used to copy a running remote server to a lokal
    # odoo instance
    #
    # dataupdate:
    # -----------
    # this copies both an odoo db and the related file data structure from
    # a remote server to a locally existing (buildout created) server.
    # the needed info is gathered from diverse sources:
    # local_data.py
    # -------------
    # - DB_USER: the user name with which to access the local database
    #   default: the logged in user.
    # - DB_PASSWORD: the password to access the local database server
    #   default: odoo
    #   If the option -p --password is used, the password in local_data is
    #   overruled.
    # remote data:
    # ------------
    # to collect data on the remote server the key remote_server is used
    #   to get info from sites.py for $SITENAME
    # - remote_url : the servers url
    # - remote_path : COLLECT it from ODOO_SERVER_DATA ??
    # local_data.REMOTE_USER_DIC:
    # ---------------------------
    # from this dictonary information on the remote server is collected
    # this is done looking up 'remote_url' in local_data.REMOTE_USER_DIC.
    # - remote_user: user to acces the remote server with
    # - remote_pw : password to access the remote user with. should normaly the empty
    #   as it is best only to use a public key.
    # - remote_path: how the odoo erverdata can be access on the remote server
    #   ??? should be created automatically
    # sites_pw.py:
    # ------------
    # the several password used for the services to be acces on the odoo instance,
    # the remote server or on the mail server can be mixed in from
    # sites_pw.py.
    # !!!! sites_pw.py should be kept separate, and should not be version controlled with the rest !!!
    #
    # it executes these steps:
    # - it executes a a command in a remote remote server in a remote shell
    #   this command starts a temporary docker container and dumps the
    #   database of the source server to its dump folder which is:
    #       $REMOTE_URL:$ODOO_SERVER_DATA/$SITENAME/dump/$SITENAME.dmp
    # - rsync this file to:
    #       localhost:$ODOO_SERVER_DATA/$SITENAME/dump/$SITENAME.dmp
    # - drop the local database $SITENAME
    # - create the local database $SITENAME
    # - restore the local datbase $SITENAME from localhost:$ODOO_SERVER_DATA/$SITENAME/dump/$SITENAME.dmp
    # - rsync the remote filestore to the local filestore:
    #   which is done with a command similar to:
    #   rsync -av $REMOTEUSER@$REMOTE_URL:$ODOO_SERVER_DATA/$SITENAME/filestore/ localhost:$ODOO_SERVER_DATA/$SITENAME/filestore/
    #
    # run_local_docker
    # ----------------
    # when the option -L --local_docker is used, data is copied from a docker container
    # running on localhost
    if opts.dataupdate or opts.dataupdate_docker:
        # def __init__(self, opts, default_values, site_name, foldernames=FOLDERNAMES)
        if opts.dataupdate:
            handler = DBUpdater(opts, default_values, site_name)
        else:
            handler = dockerHandler(opts, default_values, site_name)
        handler.doUpdate(db_update = not opts.noupdatedb)

    # transferlocal or transferdocker:
    # this is similar to dataupdate or dataupdate_docker.
    # the difference is, that the the target site is recreated from a a master site.
    # to do so, the 'slave_info' key is looked up in the server info.
    # these valuse are looked up:
    # - master_site the name of the master site, the data is to be copied from
    # - master_domain is the domain from which the master is copied
    #   not used yet
    #
    # run_local_docker
    # ----------------
    # when the option -L --local_docker is used, data is copied from a docker container
    # running on localhost
    if opts.transferlocal or opts.transferdocker:
        handler = DBUpdater(site_name)
        handler.doTransfer(opts)

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

    parser_rpc = ArgumentParser(add_help=False)
    parser = ArgumentParser(add_help=False)# ArgumentParser(usage=usage)
    parser.add_argument('--help', action=_HelpAction, help='help for help if you need some help')  # add custom help
    parser_s = parser.add_subparsers(title='subcommands', dest="subparser_name")
    #parser_site   = parser_s.add_parser('s', help='the option -s --site-description has the following subcommands', parents=[parent_parser])

    # -----------------------------------------------
    # manage rpc stuff
    # -----------------------------------------------
    #parser_remote_s = parser_remote.add_subparsers(title='remote commands', dest="rpc_commands")
    parser_rpc.add_argument("-dbh", "--dbhost",
                            action="store", dest="dbhost", default='localhost',
                            help="on what host is database running. default localhost\nif odd is running in a docker host, this value should be calculated automatically")
    parser_rpc.add_argument("-p", "--dbpw",
                            action="store", dest="dbpw", default='admin',
                            help="the password to access the database. default 'admin'")
    parser_rpc.add_argument("-dbu", "--dbuser",
                            action="store", dest="dbuser", default=DB_USER,
                            help="define user to log into database default %s" % DB_USER)
    parser_rpc.add_argument("-rpch", "--rpchost",
                            action="store", dest="rpchost", default='localhost',
                            help="define where odoo runs and can be access trough the rpc api default localhost")
    parser_rpc.add_argument("-rpcu", "--rpcuser",
                            action="store", dest="rpcuser", default='admin',
                            help="the user used to acces the running odo server using the rpc api. default admin")
    parser_rpc.add_argument("-P", "--rpcpw",
                            action="store", dest="rpcpw", default='admin',
                            help="define password for the user that accesses the running odoo server trough the rpc api. default 'admin'")
    parser_rpc.add_argument("-PO", "--port",
                            action="store", dest="rpcport", default=8069,
                            help="define the port on which the odoo server that will be accessed using the rpc api. default 8069")
    #parser_rpc.add_argument("-dbp", "--dbport",
                    #action="store", dest="dbport", default=5432,
                    #help="define db port default 5432")
    # -----------------------------------------------
    # manage sites create and update sites
    # -----------------------------------------------
    #http://stackoverflow.com/questions/10448200/how-to-parse-multiple-sub-commands-using-python-argparse
    #parser_site_s = parser_site.add_subparsers(title='manage sites', dest="site_creation_commands")
    parser_manage = parser_s.add_parser(
        'create',
        help='create is used to manage local and remote sites',
        #aliases=['c'],
        parents=[parser_rpc, parent_parser],
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
    # !!! local_docker is added to parent_parser, not parser_docker
    parent_parser.add_argument(
        "-L", "--local-docker",
        action="store_true", dest="local_docker", default=False,
        help = 'allways use a docker running locally as source when updating local data'
    )

    # -----------------------------------------------
    # manage remote server (can be localhost)
    # -----------------------------------------------
    #parser_docker_s = parser_docker.add_subparsers(title='remote commands', dest="remote_commands")
    parser_remote = parser_s.add_parser(
        'remote',
        #aliases=['r'],
        help='the command remote is used to manage the remote server.',
        parents=[parent_parser])
    parser_remote.add_argument(
        "--add-apache",
        action="store_true", dest="add_apache", default=False,
        help = 'add apache.conf to the apache configuration, also option -n --name must be set'
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

    #(opts, args) = parser.parse_args()
    parser.set_default_subparser('create')
    args, unknownargs = parser.parse_known_args()
    opts = OptsWrapper(args)
    if not opts.name and unknownargs:
        unknownargs = [a for a in unknownargs if a and a[0] != '-']
        if unknownargs:
            opts._o.__dict__['name'] = unknownargs[0]

    # is there a valid option?
    main(opts) #opts.noinit, opts.initonly)
