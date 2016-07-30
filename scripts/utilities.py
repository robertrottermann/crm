#!/usr/bin/python
# -*- encoding: utf-8 -*-

import os
import sys
import subprocess
from subprocess import PIPE
from optparse import OptionParser
import shutil
import re
import stat
from pprint import pprint
from StringIO import StringIO
import shutil
from scripts.name_completer import SimpleCompleter
from copy import deepcopy
import psycopg2
import psycopg2.extras
import urllib2

"""
create_new_project.py
---------------------
create a new odoo project so we can easily maintain a local and a remote
set of configuration files and keep them in sync.

It knows enough about odoo to be able to treat some special values correctly

# last setting contains all the setting used for the last project
from scripts.create_new_project import create_new_project, \
    check_project_exists, get_base_info, set_base_info, \
    BASE_DEFAULTS, base_info, LOGIN_INFO_TEMPLATE_FILE, get_user_info


"""

# the templatefile contains placeholder
# that will be replaced with real values
LOGIN_INFO_TEMPLATE_FILE = '%s/login_info.cfg.in'
# after strt tag we start to lok for values
START_TAG = '[login_info]'
# delimiter defines start of new value
DELIMITER = '##----'
# base path is the path from where this script is loaded
# it is wehere all config info is stored
SITE_TEMPLATE = """
    "%(site_name)s" : {
%(data)s
    },
"""


from config import ACT_USER, BASE_PATH, NEED_BASEINFO, FOLDERNAMES, \
    BASE_INFO_FILENAME, BASE_DEFAULTS, BASE_INFO, SITES, SITES_LOCAL, \
    MARKER, SITES, APACHE_PATH

try:
    from localdata import REMOTE_USER_DIC, DB_USER, DB_PASSWORD
except ImportError:
    print '*' * 80
    print 'localdata.py not found. Please create it.'
    print """it should contain:
    db_user = NAME_OF_LOCAL_DBUSER
    db_password = PASSWORD
    """
    print '*' * 80
    sys.exit()


# -------------------------------------------------------------------
# check_name
# check if name is in any of the sites listed in list_siteslist_sites
# or needed at all
# -------------------------------------------------------------------
def check_name(opts):
    need_name = [
#        "alias",
        "add_apache",
        "add_site",
        "add_site_local",
        "module_add",
#        "module_create",
        "create_container",
        "create",
#        "docker",
        "directories",
#        "list_sites",
        "name",
        "norefresh",
#        "reset",
        "simple_update",
        "dataupdate",
    ]

    no_need_name = [
        "alias",
        "module_create",
        "list_sites",
        "reset",
        "listmodules",
    ]


    if opts:
        if isinstance(opts, basestring):
            name = opts
        else:
            name = opts.name
        if not name and opts.name:
            name = opts.name
        if name:
            if name.endswith('/'):
                name = name[:-1]
            opts._o.__dict__['name'] = name
            # if not isinstance(opts, basestring):
            #     if opts.add_site:
            #         return name
            if SITES.get(name):
                return name
            if opts.add_site or opts.add_site_local:
                return name
    # no name
    # do we need a name
    nn = [n for n in need_name if opts._o.__dict__.get(n)]
    nnn = [n for n in no_need_name if opts._o.__dict__.get(n)]
    if not nn:
        if nnn:
            return True
    done = False
    cmpl = SimpleCompleter(SITES, name or opts.sitename or '')
    while not done:
        _name = cmpl.input_loop()
        if _name is None:
            done = True
            return ''
        if _name and (opts.add_site or opts.add_site_local):
            if SITES.get(_name):
                print "site %s allready exists in sites.py" % _name
            else:
                done = True
        if _name and SITES.get(_name):
            done = True
        else:
            print '%s is not defined in sites.py. you can add it with option --add-site' % _name
        if done:
            opts._o.__dict__['name'] = _name
            return _name


# ---------------------------------------------------------------------
# RPC stuff
# ---------------------------------------------------------------------

# ----------------------------------
# get_connection opens a connection to a database
def get_cursor(opts):
    if opts.dbpw:
        conn_string = "dbname='%s' user=%s host='%s' password='%s'" % (opts.dbname or opts.name, opts.dbuser,  opts.dbhost, opts.dbpw)
    else:
        conn_string = "dbname='%s' user=%s host='%s'" % (opts.dbname or opts.name, opts.dbuser,  opts.dbhost)

    conn = psycopg2.connect(conn_string)
    #cursor = conn.cursor()
    cursor_d = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return cursor_d


# ----------------------------------
# get_module_obj logs into odoo and then
# returns an object with which we can manage the list of modules
# bail out if we can not log into a running odoo site
def get_module_obj(opts):
    dbname = opts.dbname or opts.name
    try:
        import odoorpc
    except ImportError:
        print 'please install odoorpc'
        print 'execute bin/pip install -r install/requirements.txt'
        return
    #button_immediate_install(self, cr, uid, ids, context=None)
    try:
        odoo = odoorpc.ODOO(opts.rpchost, port=opts.rpcport)
        odoo.login(dbname, opts.rpcuser, opts.rpcpw)
    except odoorpc.error.RPCError:
        print 'could not login to running odoo server host: %s:%s, db: %s, user: %s, pw: %s' % (opts.dbhost, opts.dbport, dbname, opts.rpcuser, opts.rpcpw)
        return
    except urllib2.URLError:
        print 'could not login to odoo server host: %s:%s, db: %s, user: %s, pw: %s' % (opts.dbhost, opts.dbport, dbname, opts.rpcuser, opts.rpcpw)
        print 'connection was refused'
        print 'make sure odoo is running at the given address'
        return
    module_obj = odoo.env['ir.module.module']
    return module_obj

# ----------------------------------
# collect_info collects info on what modules are installed
# or need to be installed
# @req : list of required modules. If this is an empty list
#         use any module
# @uninstalled  : collect unistalled modules into this list
# @to_upgrade   :collect modules that expect upgrade into this list
def collect_info(opts, cursor, req, installed, uninstalled, to_upgrade):
    s = 'select * from ir_module_module'
    cursor.execute(s)
    rows = cursor.fetchall()
    all = not req
    updlist = []
    if opts.updateown:
        updlist = opts.updateown.split(',')
    elif opts.removeown:
        updlist = opts.removeown.split(',')
    if 'all' in updlist:
        updlist = 'all'
    for r in rows:
        n = r.get('name')
        s = r.get('state')
        i = r.get('id')
        if n in req or all:
            if n in req:
                req.pop(req.index(n))
            if s == 'installed':
                if all or updlist == 'all' or n in updlist:
                    installed.append((i, n))
                continue
            elif s in ['uninstalled', 'to install']:
                uninstalled.append((i, n))
            elif s == 'to upgrade':
                to_upgrade.append(n)
            else:
                print n, s, id


# ----------------------------------
# diff_modules
BLOCK_TEMPLATE = """
    'XXX' : [
%s
    ],
"""
def diff_installed_modules(opts, req, mod_path, rewrite, list_only=False):
    cursor = get_cursor(opts)
    if not cursor:
        return
    installed = []
    uninstalled = []
    to_upgrade = []
    collect_info(opts, cursor, req, installed, uninstalled, to_upgrade)
    bt = ''
    btl = '\n        %s,'
    if list_only:
        for t in installed:
            print t
    elif rewrite:
        f = open(mod_path, 'w')
        for t in installed:
            f.write('%s\n' % str(t))
        f.close()
    else:
        try:
            data = open(mod_path, 'r').read().split('\n')
        except IOError:
            print []
            return
        for t in installed:
            if not str(t) in data:
                bt += btl % str(t)
        if bt:
            print 'please add the following block to templates/install_blocks.py'
            print BLOCK_TEMPLATE % bt

# ----------------------------------
# install_own_modules
# own modules are listed in insyste.py under the key addons

def install_own_modules(opts, default_values, list_only=False, quiet=False):
    if list_only:
        from templates.install_blocks import INSTALL_BLOCKS
        print '\nthe following installable odoo module blocks exist:'
        print '---------------------------------------------------'
        for k in INSTALL_BLOCKS.keys():
            print '    ', k
        print '---------------------------------------------------'
        return

    site_name = check_name(opts)
    site = SITES[site_name]
    site_addons = site.get('addons')
    odoo_addons = site.get('odoo_addons')
    req = []
    module_obj = None
    if opts.installown or opts.updateown or opts.removeown or opts.listownmodules or quiet: # what else ??
        for a in (site_addons or []):
            # find out name
            name = ''
            if a.has_key('name'):
                name = a['name']
            elif a.has_key('group'):
                name = a['group']
            elif a.has_key('add_path'):
                name = a['add_path']
            if name:
                if opts.listownmodules:
                    req.append((name, a.get('url')))
                else:
                    req.append(name)
            else:
                if a and not quiet:
                    print '----> coud not detect name for %s' % a.get('url', '')

    if opts.listownmodules or quiet=='listownmodules':
        if quiet:
            return req
        print '\nthe following modules will be installed for %s:' % site_name
        print '---------------------------------------------------'
        for n, url in req:
            print '    ', n, url
        print '---------------------------------------------------'
        return

    if opts.installodoomodules:
        from templates.install_blocks import INSTALL_BLOCKS
        for o in (odoo_addons or []):
            if not INSTALL_BLOCKS.has_key(o):
                print '!' * 80
                print '%s is not a known install block' % o
                print 'check in templates/install_blocks.py what blocks are available'
                print '-' * 80
                sys.exit()
            for num, name in INSTALL_BLOCKS[o]:
                if not name in req:
                    req.append(name)
    if req:
        installed = []
        uninstalled = []
        to_upgrade = []
        module_obj = get_module_obj(opts)
        if not module_obj:
            return
        module_obj.update_list()
        cursor = get_cursor(opts)
        collect_info(opts, cursor, req, installed, uninstalled, to_upgrade)
        if req:
            print '*' * 80
            print 'the following modules where not found:', req
            print 'you probably have to download them'
            print '*' * 80
        if uninstalled:
            print 'the following modules need to be installed:', [u[1] for u in uninstalled]
            for i, n in uninstalled:
                print '*' * 80
                print 'installing: ' + n
                module_obj.browse(i).button_immediate_install()
                print 'finished installing: ' + n
                print '*' * 80
        if installed and (opts.updateown or opts.removeown):
            if opts.updateown:
                print 'the following modules need to be updated:', [u[1] for u in installed]
                for i, n in installed:
                    print '*' * 80
                    print 'upgrading: ' + n
                    module_obj.browse(i).button_immediate_upgrade()
                    print 'finished upgrading: ' + n
                    print '*' * 80
            else:
                print 'the following modules will be uninstalled:', [u[1] for u in installed]
                for i, n in installed:
                    print '*' * 80
                    print 'unistalling: ' + n
                    module_obj.browse(i).button_immediate_uninstall()
                    print 'finished unistalling: ' + n
                    print '*' * 80


# ----------------------------------
# flatten_sites
# sites can inherit settings fro other sites
# flatten_sites resolfes this inheritance tree
# @SITES            : the global list of sites
def flatten_sites(sites=SITES):
    # we allow only one inheritance level
    # check this
    for k,v in sites.items():
        inherits = v.get('inherit')
        vkeys = v.keys()
        if inherits:
            # also the inherited site must be deepcopied
            # otherwise we copy the original to our copy that is in fact nothing but a reference fo the original
            inherited = deepcopy(sites.get(inherits))
            if not inherited:
                print '*' * 80
                print 'warning !!! site description %s tries to inherit %s which does not exist' % (k, inherits)
            elif inherited.get('inherit'):
                print '*' * 80
                print 'warning !!! site description %s tries to inherit %s which does also inherit from a site. this is forbidden' % (k, inherits)
                sys.exit()
            # first copy the running site to a temporary var
            #result = v # deepcopy(v)
            # now overwrite what is in the temporary var
            #result.update(inherited)
            # now copy things back but do not overwrite "inherited" values
            # update does not work as this overwrites values that are directories
            for key, val in inherited.items():
                if isinstance(val, dict):
                    # make sure the dic exists otherwise we can not add the items
                    vvkeys = v.get(key, {}).keys()
                    if not v.has_key(key):
                        v[key] = {}
                    for val_k, val_val in val.items():
                        if isinstance(val_val, list):
                            try:
                                [v[key][val_k].append(vi) for vi in val_val if not vi in v[key][val_k] and not ('-' + vi in v[key][val_k])]
                                # clean resulting list
                                v[key][val_k] = [vi for vi in v[key][val_k] if not vi.startswith('-')]
                            except KeyError:
                                pass # inherited site has a key the inheriter does not have
                        else:
                            if val_k not in vvkeys:
                                v[key][val_k] = val_val
                elif isinstance(val, list):
                    existing = v.get(key, [])
                    v[key] = existing + [vn for vn in val if vn not in existing]
                else:
                    if key in vkeys: #['site_name', 'servername', 'db_name']:
                        continue
                    v[key] = val
            # assign the updated result to the global SITES
            #sites[k] = result
            a=1

# ----------------------------------
# collect_addon_paths
# go trough the addons in syte.py and collect
# addon_path info for the actual site. This info
# is stored in default_values
def collect_addon_paths(opts, default_values):
    name = check_name(opts)
    site = SITES[name]
    addons = site.get('addons', [])
    base_path = site.get('docker',{}).get('base_path', '/mnt/extra-addons')
    apps = []
    for addon in addons:
        if addon.get('add_path'):
            apps.append('%s/%s' % (base_path, addon['add_path']))

    default_values['add_path'] = ''
    if apps:
        default_values['add_path'] = ',' + ','.join(apps)

# ----------------------------------
# create_server_config
# create server config file in odoo_instances/SITENAME/openerp.conf
# @default_values   : default value
# @foldernames      : list of folders to create within the site foler
# ----------------------------------
def create_server_config(opts, default_values):
    name = check_name(opts)
    p = os.path.normpath('%s/%s' % (default_values['sites_home'], name))
    collect_addon_paths(opts, default_values)
    # now copy a template openerp-server.confopenerp-server.conf
    template = open('%s/templates/openerp-server.conf' % default_values['sites_home'], 'r').read()
    if os.path.exists('%s/etc/' % p):
        open('%s/etc/openerp-server.conf' % p, 'w').write(template % default_values)
    else:
        from config import FOLDERNAMES
        # create_folders will come back here, with the folders created so the writing will succed
        create_folders(opts, default_values, FOLDERNAMES)

# ----------------------------------
# create_folders
# create folder structure for site within the sites home folder
# @default_values   : default value
# @foldernames      : list of folders to create within the site foler
# ----------------------------------
def create_folders(opts, default_values, foldernames):
    name = check_name(opts)
    errors = False
    if not name:
        print 'site name not provided'
        return
    p = os.path.normpath('%s/%s' % (default_values['sites_home'], name))
    for pn in [''] + foldernames:
        try:
            pp = '%s/%s' % (p, pn)
            os.mkdir(pp)
        except:
            errors = True
            print 'could not create %s' % pp
    if errors:
        print 'not all directories could be created'
    else:
        print 'directories for %s created' % check_name(opts)

    # create server config
    create_server_config(opts, default_values)
    # p = subprocess.Popen('svn propget svn:ignore .', stdout=PIPE,shell = True)
    # res = p.communicate()
    # # propset PROPNAME PROPVAL PATH
    # if res:
    #     props = [r.strip() for r in res[0].split('\n') if r]
    #     for p in props:
    #         if p == check_name(opts):
    #             return
    #     pv = '\n'.join(props + [check_name(opts)])
    #     open('props.txt', 'w').write(pv)
    #     p = subprocess.Popen('svn propset svn:ignore -F props.txt .', stdout=PIPE,shell = True)
    #     p.communicate()
    #     if os.path.exists('props.txt'):
    #         os.unlink('props.txt')

# ----------------------------------
# get_single_value
# ask value from user
# @name         : name of the value
# @explanation  : explanation of the value
# @default      : default value
# @prompt       : prompt to display
# ----------------------------------
def get_single_value(
        name,
        explanation,
        default,
        prompt = '%s [%s]:',
    ):
    # get input from user for a single value. present expanation and default value
    print '*' * 50
    print explanation
    result =  raw_input(prompt % (name, default))
    if not result:
        result = default
    return result

def set_base_info(info_dic, filename):
    "write bas info back to the config folder"
    info = 'base_info = %s' % info_dic
    open(filename, 'w').write(info)

def get_base_info(base_info, base_defaults):
    "collect base info from user, update base_info"
    for k, v in base_defaults.items():
        name, explanation, default = v
        # use value as stored, default otherwise
        default = BASE_INFO.get(k, default)
        base_info[k] =  get_single_value(name, explanation, default)

# ----------------------------------
# update_base_info
# collects localdata that will be stored in config/base_info.py
# @base_info_path   : path to config/base_info.pyconfig/base_info.py
# @default_values   : dictionary with default values
# ----------------------------------
def update_base_info(base_info_path, defaults):
    base_info = {}
    get_base_info(base_info, defaults)
    set_base_info(base_info, base_info_path)
    print '%s created' % base_info_path
    print 'please restart'

# ----------------------------------
# list_sites
# list sitenames listed in the sites_dic
# @sites_dic    : dictionary with info about sites
#                 this is the combination of sites.py and local_sites.py
# ----------------------------------
def list_sites(sites_dic):
    keys = sites_dic.keys()
    keys.sort()
    for key in keys:
        if sites_dic[key].get('is_local'):
            print '%s (local)' % key
        else:
            print key

# ----------------------------------
# add_site_to_sitelist
# add new site description to sites.py
# @opts             : option instance
# @default_values   : dictionary with default values
# ----------------------------------
def add_site_to_sitelist(opts, default_values):
    default_values['marker'] = MARKER
    template = open('%s/templates/newsite.py' % BASE_PATH, 'r').read() % default_values
    # now open sites.py as text and replace the marker with the templae which allready has a new marker
    if opts.add_site:
        m = re.compile(r'\n%s' % MARKER)
        sites = open('%s/sites.py' % BASE_PATH).read()
        if not m.search(sites):
            print "ERROR: the marker could not be found in sites.py"
            print "make sure it exists and starts at the beginning of the line"
            return
        open('%s/sites.py' % BASE_PATH, 'w').write(m.sub(template, sites))
        print "%s added to sites.py" % check_name(opts)
    elif opts.add_site_local:
        # we add to sites local
        # we read untill we find an empty }
        lines = open('%s/sites_local.py' % BASE_PATH).read().split('\n')
        f = open('%s/sites_local.py' % BASE_PATH, 'w')
        m = re.compile(r'^}\s*$')
        for line in lines:
            if m.search(line):
                f.write(template)
                f.write(line + '\n')
                f.close()
                break
            else:
                f.write(line + '\n')


# ----------------------------------
# flatten_site_dic
# check whether a site dic has all substructures
# flatten them into a dictonary without substructures
# @ site_name       : dictonary to flatten
# ----------------------------------
def flatten_site_dic(site_name, sites=SITES):
    res = {}
    site_dic = sites.get(site_name)
    if not site_dic:
        print 'error: %s not found in provided list of sites' % site_name
        return
    sd = site_dic.copy()
    parts = [
        'docker',
        'remote_server',
        'apache',
    ]
    vparts = [
        'slave_info',
    ]
    both = parts + vparts
    for k, v in sd.items():
        if not k in both:
            res[k] = v
    for p in parts:
        pDic = sd.get(p)
        if not pDic:
            print 'error: %s not found site description for %s' % (p, site_name)
            return
        for k, v in pDic.items():
            res[k] = v
    for p in vparts:
        pDic = sd.get(p, {})
        for k, v in pDic.items():
            res[k] = v
    print res
    return res

# ----------------------------------
# add_site_to_apache
# create virtual host entry for apache
# if user is allowed to wite to the apache directory, add it to
#   sites_available and sites_enabled
# if not, just print it out
# @opts             : option instance
# @default_values   : dictionary with default values
# ----------------------------------
HA = """
%s
"""
HL = "    ServerAlias %s\n"
def add_site_to_apache(opts, default_values):
    default_values['marker'] = MARKER
    site_name = check_name(opts)
    if not SITES.has_key(site_name):
        print '%s is not known in sites.py' % site_name
        return
    df = deepcopy(default_values)
    site_info = flatten_site_dic(site_name)
    df['vservername'] = site_info.get('vservername', '    www.%s.ch' % site_name)
    aliases_string = ''
    for alias in site_info.get('vserveraliases', []):
        aliases_string += HL % alias
    df['serveralias'] = aliases_string.rstrip()
    df.update(site_info)
    template = open('templates/apache.conf', 'r').read() % df
    #template = template % d

    print template
    try:
        apa = '%s/sites-available/%s.conf' % (APACHE_PATH, site_name )
        ape = '%s/sites-enabled/%s.conf' % (APACHE_PATH, site_name )
        open(apa, 'w').write(template)
        if os.path.exists(ape):
            try:
                os.unlink(ape)
            except:
                pass # exists ??
        try:
            os.symlink(apa, ape)
        except:
            pass
        print "%s added to apache" % site_name
        print 'restart apache to activate'
    except:
        print "could not write %s" % apa

# ----------------------------------
# module_add
# add module to sitey.py for a site, create it if opts.module_create
# if user is allowed to wite to the apache directory, add it to
#   sites_available and sites_enabled
# if not, just print it out
# @opts             : option instance
# @default_values   : dictionary with default values
# @site_values      : values for this site as found in systes.py
# @module_name      : name of the new module
# ----------------------------------
def module_add(opts, default_values, site_values, module_name):
    # we start opening the sites.py as text file
    if default_values['is_local']:
        sites_path = '%s/sites_local.py' % default_values['sites_home']
    else:
        sites_path = '%s/sites.py' % default_values['sites_home']
    sites_str = open(sites_path, 'r').read()
    # startmach is a line with nothin but:
    #    "breitschtraeff9" : {
    start_match = re.compile(r'\s+"%(site_name)s"\s*:\s\{' % default_values )
    # startmach is a line with nothin but:
    #    },
    end_match = re.compile(r'^\s*},\s*$')
    # separate sites.py into lines before and after actual site
    lines = sites_str.split('\n')
    pref_lines = []
    sub_lines = []
    started = False
    before = True # we add lines to before
    for line in lines:
        if start_match.match(line):
            started = True
        if started:
            # we only check if fiished, if started = true
            if end_match.match(line):
                started = False
                before = False
            continue
        # we are not within the started block
        if before:
            pref_lines.append(line)
        else:
            sub_lines.append(line)
    # add new module to the list of modules
    mlist = site_values.get('addons', [])
    if not module_name in mlist:
        mlist.append(module_name)
        site_values['addons'] = mlist
        # create dict as text to be patched between pref_ & sub_lines
        buffer = StringIO()
        pprint(site_values, indent=8, stream=buffer)
        site_string = buffer.getvalue()
        # remove opening/closing brackets
        site_string = ' ' + site_string[1:-2] + ','
        new_site = SITE_TEMPLATE % {'data' : site_string, 'site_name' : default_values['site_name']}
        # construct new filecontent of systes.py by conatenating its three elements
        data = '\n'.join(pref_lines) + new_site + '\n'.join(sub_lines)
        # write that thing
        open(sites_path, 'w').write(data)
    # if opts.module_create we create the modul using odos scaffolding facility
    if opts.module_create:
        inner = default_values['inner']
        # check wheter the addon directory exists
        # this directory is create by dosetup.py
        addons_path = '%(inner)s/%(site_name)s_addons' % default_values
        module_path = '%s/%s' % (addons_path, module_name)
        if not os.path.exists(addons_path):
            print '%s does not exist'
            return
        if os.path.exists(module_path):
            print 'module %s allready exists'
            return
        # fine, we can go ahead
        # hopefully odoo is at its standard place
        #odoo_path = '%(inner)s/parts/odoo/odoo.py' % default_values
        runner_path = '%(inner)s/bin/odoorunner.py' % default_values
        # usage: odoorunner.py scaffold [-h] [-t TEMPLATE] name [dest]
        cmdline = '%s scaffold %s %s' % (runner_path, module_name, addons_path)
        print cmdline
        cur_dir = os.getcwd()
        os.chdir(default_values['inner'])
        p = subprocess.Popen(cmdline, stdout=PIPE,shell = True)
        res = p.communicate()
        os.chdir(cur_dir)
        print 'added skeleton to %s' % module_path

# ----------------------------------
# construct_defaults
# construct defaultvalues for a site
# @site_name        : name of the site
# ----------------------------------
def construct_defaults(site_name, opts = None):
    import copy
    # construct a dictonary with default values
    # some of the values in the imported default_values are to be replaced
    # make sure we can do this more than once
    from templates.default_values import default_values as d_v
    default_values = copy.deepcopy(d_v)
    # first set default values that migth get overwritten
    # local sites are defined in local_sites and are not added to the repository
    is_local = not(SITES_LOCAL.get(site_name) is None)
    default_values['is_local'] = is_local
    # as what user will the user eventually log into the database
    default_values['db_user'] = ACT_USER
    # sites_home is where all sites directories are kept
    # eg ~/odoo_sites
    default_values['sites_home'] = BASE_PATH
    # the site_name is what the user with option -n and was checked by check_name
    default_values['site_name'] = site_name
    default_values.update(BASE_INFO)
    if isinstance(site_name, basestring):
        if opts:
            if (not opts.add_site) and (not opts.add_site_local) and (not opts.listmodules):
                default_values.update(SITES.get(site_name))
        else:
            default_values.update(SITES.get(site_name))
    site_base_path = os.path.normpath(os.path.expanduser('%(project_path)s/%(site_name)s/' % default_values))
    default_values['base_path'] = site_base_path #/home/robert/projects/afbsecure/afbsecure/parts/odoo
    #'data_dir' : '',
    default_values['data_dir'] = '%(sites_home)s/%(site_name)s' % default_values
    #'db_name' : '',
    default_values['db_name'] = site_name
    #'outer' : '',
    default_values['outer'] = '%s/%s' % (BASE_INFO['project_path'], site_name)
    #'inner' : '',
    default_values['inner'] = '%(outer)s/%(site_name)s' % default_values
    # 'addons_path' : '',
    default_values['addons_path'] = '%(base_path)s/parts/odoo/openerp/addons,%(base_path)s/parts/odoo/addons,%(sites_home)s/%(site_name)s/addons' % default_values
    # if we are using docker, the addon path is very different
    if opts.dataupdate_docker:
        # what fore do we use this ??
        default_values['addons_path'] = '/mnt/extra-addons,/usr/lib/python2.7/dist-packages/openerp/addons'
    default_values['skeleton'] = '%s/skeleton' % BASE_PATH
    # add modules that must be installed using pip
    _s = {}
    if is_local:
        _s = SITES_LOCAL.get(site_name)
    else:
        if SITES.get(site_name):
            _s = SITES.get(site_name)
    site_addons = _s.get('addons', [])
    pip_modules = _s.get('pip', [])
    skip_list   = _s.get('skip', {}).get('addons', [])

    pm='\n'
    if pip_modules:
        for m in pip_modules:
            pm += '%s\n' % m
    default_values['pip_modules'] = pm
    default_values['site_addons'] = _construct_sa(
        site_name, copy.deepcopy(site_addons),skip_list)

    return default_values

def _construct_sa(site_name, site_addons, skip_list):
    added = []
    name = ''
    for a in (site_addons or []):
        # find out name
        if a.has_key('name'):
            name = a['name']
        elif a.has_key('add_path'):
            name = a['add_path']
        elif a.has_key('group'):
            name = a['group']
        if name and name in skip_list:
            continue
        ap = a.get('add_path')
        if ap:
            p = os.path.normpath('%s/%s/addons/%s' % (BASE_PATH, site_name, ap))
        else:
            p = os.path.normpath('%s/%s/addons' % (BASE_PATH, site_name))
        if not p in added:
            added.append(p)
    return '\n'.join(['    local %s' %a for a in added])

from vcs.git import GitRepo
from vcs.svn import SvnCheckout
# ----------------------------------
# checkout_sa
# get addons from repository
# @opts   : options as entered by the user
# ----------------------------------
def checkout_sa(opts):
    result = []
    site_addons = []
    is_local = not(SITES_LOCAL.get(opts.name) is None)
    _s = SITES.get(opts.name)
    if is_local:
        _s = SITES_LOCAL.get(opts.name)
    site_addons = _s.get('addons', [])
    skip_list   = _s.get('skip', {}).get('addons', [])
    for site_addon in site_addons:
        # find out name
        name = ''
        if site_addon.has_key('name'):
            name = site_addon['name']
        elif site_addon.has_key('add_path'):
            name = site_addon['add_path']
        elif site_addon.has_key('group'):
            name = site_addon['group']
        if name and name in skip_list:
            continue
        if site_addon:
            url = site_addon['url']
            branch = site_addon.get('branch', 'master')
            target = os.path.normpath('%s/%s/addons' % (BASE_PATH, opts.name))
            if site_addon.has_key('group'):
                target = '%s/%s' % (target, site_addon['group'])
            target = os.path.normpath(target)
            if site_addon.get('type') == 'git':
                gr = GitRepo(target, url)
                gr(branch)
            if site_addon.get('type') == 'svn':
                sv = SvnCheckout(target, url)
                sv(branch)
    return result

# =============================================================
# create site stuff
# =============================================================
def create_virtual_env(target):
    "create a virtual env within the new project"
    adir = os.getcwd()
    os.chdir(target)
    # create virtual env
    cmd_line = ['virtualenv', 'python']
    p = subprocess.Popen(cmd_line, stdout=PIPE)
    p.communicate()
    os.chdir(adir)

def get_config_info(default_values, opts=None):
    """
    collect values needed to put into the openerp.cfg file
    """
    # read the login_info.py.in
    # in this file, all variables are of the form $(VARIABLENAME)$
    # replace_dic is constructed in get_user_info_base->build_replace_info
    # the names to replace are defined globaly as REPLACE_NAMES
    p1 = LOGIN_INFO_TEMPLATE_FILE % default_values['inner']
    p2 = LOGIN_INFO_TEMPLATE_FILE % default_values['skeleton']
    #if not os.path.exists(p1) or (opts and opts.simple_update):
    return open(p2, 'r').read() % default_values

def check_project_exists(default_values, opts):
    # check if project exists
    skeleton = default_values['skeleton']
    outer = default_values['outer']
    inner = default_values['inner']
    if not os.path.exists(inner):
        create_new_project(default_values, opts)
    do_copy(skeleton, outer, inner, opts)
    if opts.git_add:
        # was svn_add, must be rewritten
        adir = os.getcwd()
        os.chdir('%s/..' % default_values['outer'])
        p = subprocess.Popen(['svn', 'add', default_values['outer'], '--depth=files'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        p = subprocess.Popen(['svn', 'add', '%s/documents' % default_values['outer']],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p = subprocess.Popen(['svn', 'propset', 'svn:ignore', opts.name, default_values['outer']],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        print out, err
        # make sure wirtual env exist even when the project was red from the repository
    create_virtual_env(inner)

def create_new_project(default_values, opts):
    "ask for project info, create the structure and copy the files"
    skeleton = default_values['skeleton']
    outer = default_values['outer']
    inner = default_values['inner']
    # create project folders
    # create sensible error message
    # check whether projects folder exists
    pp = default_values['project_path']
    if not os.path.exists(pp) and not os.path.isdir(pp):
        # try to create it
        try:
            os.makedirs(pp)
        except OSError:
            print '*' * 80
            print 'could not create %s' % pp
            sys.exit()
    for p in [outer, inner]:
        if not os.path.exists(p):
            os.mkdir(p)
    ppath_ini = '%s/__init__.py' % outer
    if not os.path.exists(ppath_ini):
        open(ppath_ini, 'w').close()
    #create virtualenv
    # copy files
    #create_virtual_env(inner)

def do_copy(source, outer_target, inner_target, opts):
    # now copy files
    from skeleton.files_to_copy import FILES_TO_COPY
    simple_update = False # only copy some files so we can rerun dosetup
    try:
        simple_update = opts.simple_update
    except:
        pass
    if simple_update:
        handle_file_copy_move(source, inner_target, FILES_TO_COPY['simple_copy'], opts)
    else:
        handle_file_copy_move(source, inner_target, FILES_TO_COPY['project'], opts)
    # create directories and readme in the project home
    if outer_target:
        handle_file_copy_move('', outer_target, FILES_TO_COPY['project_home'], opts)


def handle_file_copy_move(source, target, filedata, opts):
    # if overwrite is set, existing files are overwritten
    # if make_links is set links to dosetup.py and update_localdb.py are created, otherwise the files are copied
    try:
        overwrite = opts.overwrite
        make_links = not opts.update_nolinks
    except AttributeError as e:
        overwrite = True
        make_links = False
    for fname, tp in filedata.items():
        # F = File
        # X = File set executable bit
        # L = Linkpath)

        # D = Folder
        # T = Touch
        # R = copy and rename
        # '$FILE$' link to the source
        try:
            cmd = ''
            spath = fname
            if source:
                spath = '%s/%s' % (source, fname)
            tpath = '%s/%s' % (target, fname)
            if isinstance(tp, tuple):
                tp, cmd = tp
                if cmd:
                    if cmd == '$FILE$':
                        if make_links:
                            if os.path.exists(tpath):
                                os.remove(tpath)
                            os.symlink(spath, tpath)
                            continue
                        else:
                            # copy like normal file
                            # allways overwrite
                            if os.path.exists(tpath):
                                os.remove(tpath)
                            shutil.copyfile(spath, tpath)
                if tp == 'L':
                    # does the target exist and do we want to overwrite it?
                    if os.path.exists(tpath) and not os.path.islink(tpath) and make_links:
                        # we want to make links, but target is not a link
                        # so we remove it
                        os.remove(tpath)
                    elif os.path.exists(tpath) and overwrite:
                        # target exist, but we want to renew it
                        os.remove(tpath)
                    # cmd is the link
                    # change to the target
                    if not os.path.exists(tpath):
                        # link was not copied yet or has been remove due to the overwrite flag
                        adir = os.getcwd()
                        os.chdir(target)
                        try:
                            os.symlink(cmd, tpath)
                        except OSError as e:
                            print '*' * 80
                            print str(e)
                            print 'cmd:', cmd
                            print 'tpath:', tpath
                            print '*' * 80
                        os.chdir(adir)
                if tp == 'R':
                    # copy and rename
                    tpath = '%s/%s' % (target, cmd) #cmd is the name of the new file
                    # only overwrite if overwrite is set
                    if overwrite and os.path.exists(tpath):
                        os.remove(tpath)
                    if overwrite or (not os.path.exists(tpath)):
                        shutil.copyfile(spath, tpath)

            elif isinstance(tp, dict):
                # new directory
                newsource = '%s/%s' % (source, fname)
                newtarget = '%s/%s' % (target, fname)
                if not os.path.exists(newtarget):
                    os.mkdir(newtarget)
                handle_file_copy_move(newsource, newtarget, tp, opts)
            else:
                # this is just a simple command ..
                if tp == 'F':
                    # a normal file
                    # only overwrite if overwrite is set
                    if overwrite and os.path.exists(tpath):
                        os.remove(tpath)
                    if overwrite or (not os.path.exists(tpath)):
                        shutil.copyfile(spath, tpath)
                elif tp == 'X':
                    # a normal file, but set execution flag
                    # only overwrite if overwrite is set
                    if overwrite and os.path.exists(tpath):
                        os.remove(tpath)
                    if overwrite or (not os.path.exists(tpath)):
                        shutil.copyfile(spath, tpath)
                    # set executable
                    st = os.stat(tpath)
                    os.chmod(tpath, st.st_mode | stat.S_IEXEC)
                elif tp == 'L':
                    if overwrite and os.path.exists(tpath):
                        os.remove(tpath)
                    # a link
                    if not os.path.exists(tpath):
                        shutil.copyfile(spath, tpath)
                elif tp == 'D':
                    # a folder to create
                    #if overwrite and os.path.exists(tpath):
                        #shutil.rmtree(tpath, True)
                    if not os.path.exists(tpath):
                        os.mkdir(tpath)
                elif tp == 'T':
                    # just touch to create
                    open(tpath, 'a').close()
        except IOError as e:
            print str(e)

# =============================================================
# add site to bash_aliases
# =============================================================
OOIN = """
# odoo
alias  ooin="cd %s"

"""
PROD = """
# products
alias  prod="cd %s"

"""
ALIAS = """
# %(lname)s
alias  %(sname)s="cd %(ppath)s/%(lname)s/%(lname)s"
alias  %(sname)shome="cd %(ppath)s/%(lname)s/"
alias  %(sname)sa="cd cd %(ppath)s/%(lname)s/%(lname)s/%(sname)s_addons"
"""
ALIAS_LINE = 'alias  %(sname)s="cd %(path)s"\n'
AMARKER = '##-----alias-marker %s-----##'
ABLOCK = """%(aliasmarker_start)s
# please do not change the lines between the two markers
# they are managed by the createsite scripts
%(alias_list)s
%(aliasmarker_end)s"""
ALIAS_LENGTH = 4
def create_aliases(opts, default_values):
    pp = default_values['project_path']
    oop = BASE_PATH
    # shortnamesconstruct
    alias_names = [n for n in SITES.keys() if len(n) <= ALIAS_LENGTH]
    names = SITES.keys()
    names.sort()
    long_names = alias_names
    for n in names:
        if n in alias_names:
            continue # the  short ones
        try_length = ALIAS_LENGTH
        while n[:try_length] in alias_names:
            try_length += 1
            # we will for sure find a key ..
        alias_names.append(n[:try_length])
        long_names.append(n)
    result = ALIAS_LINE % {'sname' : 'pro', 'path' : pp }
    result += ALIAS_LINE % {'sname' : 'ooin', 'path' : oop }
    for i in range(len(alias_names)):
        if os.path.exists('%s/%s' % (pp, long_names[i])):
            result += ALIAS % {
                'sname' : alias_names[i],
                'lname' : long_names[i],
                'ppath' : pp,
            }
    return result


def add_aliases(opts, default_values):
    # # check if project exists
    # inner = default_values['inner']
    # if not os.path.exists(inner):
    #     # project does not yet exist, just return
    #     return
    # # remember where we came from
    # adir = os.getcwd()
    # os.chdir('%s' % inner)
    # p = subprocess.Popen(['bin/python', 'alias.py'],
    #                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # out, err = p.communicate()
    # return True
    pp = default_values['project_path']
    oop = BASE_PATH
    marker_start = AMARKER  % 'start'
    marker_end = AMARKER  % 'end'
    # where do we want to add our aliases?
    alias_script = "bash_aliases"
    try:
        dist = open("/etc/lsb-release").readline()
        dist = dist.split("=")
        print dist[1]
        if dist[1].strip("\n") == "LinuxMint":
            alias_script = "bashrc"
        elif dist[1].strip("\n") == "Ubuntu":
            alias_script = "bash_aliases"
    except:
        print 'could not determine linux distribution'
        pass
    home = os.path.expanduser("~")
    alias_path = '%s/.%s' % (home, alias_script)
    try:
        data = open(alias_path, 'r').read()
    except:
        data = ''
    data = data.split('\n')
    alias_str = ''
    # loop over data and add lines to the result untill we see the marker
    # then we loop untill we get the endmarker or the end of the file
    start_found = False
    end_found = False
    for line in data:
        if not start_found:
            if line.strip() == marker_start:
                start_found = True
                continue
            alias_str += '%s\n' % line
        else:
            if line.strip() == marker_end:
                end_found = True
                start_found = False
    # we no have all lines without the constucted alias in alias_str
    # we add a new block of aliases to it
    alias_str += ABLOCK % {
        'aliasmarker_start' : marker_start,
        'aliasmarker_end' : marker_end,
        'alias_list' : create_aliases(opts, default_values),
        'ppath' : pp,
        }

    open(alias_path, 'w').write(alias_str)



# =============================================================
# handle docker stuff
# =============================================================
def run_commands(opts, cmd_lines, shell=True):
    from localdata import DB_USER, DB_PASSWORD
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


def update_docker_info(default_values, name, url='unix://var/run/docker.sock', required=False, start=True):
    cli = default_values.get('docker_client')
    if not cli:
        from docker import Client
        cli = Client(base_url=url)
        default_values['docker_client'] = cli
    registry = default_values.get('docker_registry', {})
    info = cli.containers(filters={'name' : name}, all=1)
    if info:
        info = info[0]
        if info['State'] != 'running':
            if start:
                cli.restart(name)
                info = cli.containers(filters={'name' : name})
                if not info:
                    raise ValueError('could not restart container %s', name)
                info = info[0]
            elif required:
                raise ValueError('container %s is stopep, no restart is requested', name)                
        registry[name] = info
    else:
        if required:
            raise ValueError('required container:%s does not exist' % name)
    default_values['docker_registry'] = registry

def update_container_info(default_values, opts):
    sys.path.insert(0, '..')
    try:
        from docker import Client
    except ImportError:
        print '*' * 80
        print 'could not import docker'
        print 'please run bin/pip install -r install/requirements.txt'
        return
    name = opts.name
    site_info = SITES[name]
    docker = site_info.get('docker')
    if not docker or not docker.get('container_name'):
        print 'the site description for %s has no docker description or no container_name' % opts.name
        return
    # collect info on database container which allways is named 'db'
    update_docker_info(default_values, 'db', required=True)
    update_docker_info(default_values, docker['container_name'])
    #check whether we are a slave
    if site_info.get('slave_info'):
        master_site = site_info.get('slave_info').get('master_site')
        if master_site:
            update_docker_info(default_values, master_site)

def check_and_create_container(default_values, opts):
    update_container_info(default_values, opts)
    # if we land here docker info is acessible from sites.py
    name = opts.name
    container_name = SITES[name]['docker']['container_name']
    odoo_port = SITES[name]['docker']['odoo_port']
    if not default_values['docker_registry'].get(container_name):
        from templates.docker_container import docker_template
        docker_info = {
            'odoo_port' : odoo_port,
            'site_name' : name,
            'container_name' : container_name,
            'remote_path' : SITES[name]['remote_server']['remote_path'],
            'odoo_image_version' : SITES[name]['docker']['odoo_image_version'],
        }
        docker_template = docker_template % docker_info
        mp = default_values.get('docker_path_map')
        if mp and ACT_USER != 'root':
            try:
                t, s = mp
                docker_template = docker_template.replace(s, t)
            except:
                pass
        run_commands(opts, [docker_template])
        print docker_template
    else:
        print 'container %s allready running' % name

# =============================================================
# get server info from site description
# =============================================================
def get_remote_server_info(opts, use_name=None):
    if not use_name:
        name = opts.name
    else:
        # in transfer, we do not want to use the name
        # provided in opts ..
        name = use_name
        if not SITES.get(name):
            print '*' * 80
            print 'provided use_name=%s is not valid on this server' % use_name
            raise ValueError('provided use_name=%s is not valid on this server' % use_name)

    d = SITES[name].copy()
    serverDic = d.get('remote_server')
    if not serverDic:
        print '*' * 80
        print 'the site description for %s has no remote_server description' % opts.name
        print 'please add one'
        print '*' * 80
        serverDic = {
            'remote_url'    : d['remote_url'],
            'remote_path'   : d['remote_path'],
            'remote_user'   : d['remote_user'],
        }
    # if the remote url is overridden, replace it now
    if opts._o.__dict__.has_key('remote_url') and opts.overrideremote:
        serverDic['remote_url'] = opts.overrideremote
    # now we have to make sure, that we use the local users credentials
    remote_url = serverDic['remote_url']
    # what credentials does the actual user have to acces the remote host?
    remote_user_dic = REMOTE_USER_DIC.get(remote_url)
    if not remote_user_dic:
        print '*' * 80
        print 'there is no access info for server %s' % remote_url
        print 'please add it to your local info'
        print '*' * 80
        return {}
    serverDic.update(remote_user_dic)
    return serverDic
