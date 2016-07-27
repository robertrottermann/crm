#!bin/python
# -*- encoding: utf-8 -*-
import os
import sys
BASE_PATH = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
BASE_INFO = {}
import getpass
ACT_USER = getpass.getuser()
try:
    from base_info import base_info as BASE_INFO
    NEED_BASEINFO = False
except ImportError:
    NEED_BASEINFO = True
# what folders do we need to create in odoo_sites for a new site
FOLDERNAMES = ['addons','dump','etc','filestore', 'log']
# base info filename points to file where some default values are stored
# base_info = {'project_path': '/home/robert/projects', 'skeleton': 'odoo/skeleton'}
BASE_INFO_NAME = 'base_info'
BASE_INFO_FILENAME = '%s/config/%s.py' % (BASE_PATH, BASE_INFO_NAME)

# base defaults are the defaults we are using for the base info if they where not set
BASE_DEFAULTS = {
    #name, explanation, default
    'project_path' : (
        'project path',                 # display
        'path to the projects',         # help
        '/home/%s/projects' % ACT_USER  # default
    ),
    'docker_path_map' : (
        'docker path map. use , to separate parts',              # disply
        'docker volume mappings when docker is run locally', # help
        ACT_USER == 'root' and () or ('/home/%s/' % ACT_USER, '/root/')
    )
}
# base defaults are the defaults we are using for the base info if they where not set
PROJECT_DEFAULTS = {
    #name, explanation, default
    'projectname' : ('project name', 'what is the project name', 'projectname'),
    'odoo_version' : ('odoo version', 'version of odoo', '9.0'),
}
# sites is a combination created from "regular" sites listed in sites.py
# an a list of localsites listed in local_sites.py
from sites import SITES, SITES_L as SITES_LOCAL

try:
    from localdata import REMOTE_USER_DIC, APACHE_PATH, DB_USER, DB_PASSWORD
except ImportError:
    print 'please create localdata.py'
    print 'it mus have values for REMOTE_USER_DIC, APACHE_PATH, DB_USER, DB_PASSWORD'
    print 'use localdata.py.in as template'
    sys.exit()

# MARKER is used to mark the position in sites.py to add a new site description
from sites import MARKER
# file to which site configuration will be written
LOGIN_INFO_FILE_TEMPLATE = '%s/login_info.cfg.in'

# file to which pip requirements will be written
REQUIREMENTS_FILE_TEMPLATE = '%s/install/requirements.txt'
