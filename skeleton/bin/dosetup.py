#!/usr/bin/python
# -*- encoding: utf-8 -*-

import glob
import os
import sys
import subprocess
from subprocess import PIPE
from optparse import OptionParser
import shutil
import inspect

"""
this script sets up a new odoo project within the redcor project structure
it makes sure that all varaible-placeholder that are left from creating the structure and copying templtes
are replaced with the actual values.
Furthermore it creates login_info.cfg from login_info.cfg.in.
login_info.cfg is not overwritten automatically. Use --force to do so.
"""
SKIP_DIRS = [
    'anybox.recipe.openerp',
    'bin',
    'bootstrap.py',
    'develop-eggs',
    'downloads',
    'etc',
    'parts',
    'python',
    'sql_dumps',
]

TAG = '%s(PROJECTNAME)%s' % ('$', '$') #make sure the tag definition does not replace it self
UTAG = '$(USERNAME)$'
#SKELETON_PATH = 'odoo/skeleton'
SKELETON_NAME = 'skeleton'
DEBUG = True

filename = inspect.getframeinfo(inspect.currentframe()).filename
# PROJECT_HOME is the folder in which the project is created
PROJECT_HOME  = os.path.split(os.path.dirname(os.path.abspath(filename)))[0]
# PROJECT_LIST_DIR the folder that houses all projects
PROJECT_LIST_DIR = os.path.split(os.path.split(PROJECT_HOME)[0])[0]
SVN_IGNORES = {
    '.' : [
        '.dosetup',
        '.installed.cfg',
        'anybox.recipe.openerp',
        'bin/buildout',
        'bin/upgrade_openerp',
        'develop-eggs',
        'downloads',
        'eggs',
        'etc',
        'login_info.cfg',
        'parts',
        'python',
        'upgrade.py',
    ],
    'bin' : [
        'gevent_openerp',
        'python_openerp',
        'start_openerp',
        'buildout',
        'upgrade_openerp',

    ],
}
def handle_svn_ignores():
    # we loop trough the list of ignores for every directory in SVN_IGNORES
    # and check whether we need to add it
    for p, files in SVN_IGNORES.items():
        # keep a pointer to actual directory
        actual = os.getcwd()
        # change to new dir if approriate
        if  p != '.':
            nd = '%s/%s' % (actual, p)
            os.chdir(nd)
        cmd_line = 'svn propget svn:ignore .'
        p = subprocess.Popen(cmd_line, stdout=PIPE, shell=True)
        result = p.communicate()[0]
        rlist = result.split('\n')
        # check wheter files are allready ignored
        # add them if appropriate
        added = False
        for f in files:
            if f not in rlist:
                added = True
                rlist.append(f)
        rlist = [r for r in rlist if r.strip()]
        if added:
            filename = '/tmp/guess_my_name.%s.txt' % os.getpid()
            temp = open(filename, 'w+b')
            temp.write('\n'.join(rlist))
            temp.close()
            cmd_line = 'svn propset svn:ignore -F %s .' % filename
            p = subprocess.Popen(cmd_line, stdout=PIPE, shell=True)
            p.communicate()
            os.remove(filename)
        # return to actual directory
        os.chdir(actual)

def replaceTags(dlist, projectname, replace_user):
    data = dlist[0]
    replaced = False
    if data.find(TAG) > -1:
        data = data.replace(TAG, projectname)
        replaced = True
    if data.find(UTAG) > -1:
        if not replace_user and (DEBUG):
            replace_user = projectname
        if replace_user:
            data = data.replace(UTAG, replace_user)
        replaced = True
    if replaced:
        dlist[0] = data
    return replaced

def doUpdate(root, name, PROJECTNAME, force=False):
    fpath = os.path.join(root, name)
    data = open(fpath, 'r').read()
    replace_user = ''
    try:
        replace_user = os.getlogin()
    except:
        import getpass
        replace_user = getpass.getuser()
    fpath_ori = ''
    if name == 'login_info.cfg.in':
        fpath_ori = fpath
        fpath = os.path.join(root, 'login_info.cfg')

    dlist = [data]
    if replaceTags(dlist, PROJECTNAME, replace_user):
        # here we land, if a tag was to replace
        plist = [fpath_ori, fpath]
        if PROJECTNAME == SKELETON_NAME:
            # do not overwrite 'login_info.cfg.in'
            plist = [fpath]
        for fp in plist:
            if fp:
                f = open(fp, 'w')
                f.write(dlist[0])
                f.close()
        print('File:', fpath, ' updated')
    elif fpath_ori:
        # here we land, if project was allredy constructed
        #just make sure that there is a 'login_info.cfg'
        if not os.path.exists(fpath) or force:
            shutil.copyfile(fpath_ori, fpath)
            print('File:', fpath_ori, ' copied to ', fpath)
        else:
            print '*' * 80
            print 'login_info.cfg not overwritten. Use --f --force to replace it '
            print '*' * 80

def  skip_root(root, home):
    # we want to check whether root is in SKIP_DIRS
    # but we must be carefull not to skipp all files when any of the names in SKIP_DIRS
    # are part of the path to the project
    if root.startswith(home):
        root = root[len(home):]
    parts = root.split(os.path.sep)
    for part in parts:
        if part in SKIP_DIRS:
            return True
    return False


def main(opts): #nosetup=False, onlysetup=False):
    nosetup = opts.noinit
    onlysetup = opts.initonly
    force = opts.force
    # replace all placeholder to the name of the actual directory
    print PROJECT_HOME
    PROJECTNAME = os.path.split(PROJECT_HOME)[-1]
    if opts.ignores:
        handle_svn_ignores()
        print 'svn:ignores set'
        return()
    if not onlysetup:
        for root, dirs, files in os.walk(PROJECT_HOME, topdown=False):
            for name in files:
                if skip_root(root, PROJECT_HOME):
                    continue
                fpath = os.path.join(root, name)
                if os.path.islink(fpath):
                    continue
                doUpdate(root, name, PROJECTNAME, force)

    # create folder for odoo_addons
    try:
        os.mkdir('%s_addons' % PROJECTNAME)
    except:
        pass # allready exists

    addonsline = ['svn', 'add', '%s_addons' % PROJECTNAME]

    # create virtual env
    if nosetup:
        setupline = []
    else:
        setupline = ['virtualenv', 'python']

    if onlysetup:
        cmd_lines = [['virtualenv', 'python'],['python/bin/python', 'bootstrap.py'],]
    else:
        cmd_lines = [
            # delete the local database(s)
            setupline,
            ['python/bin/pip', 'install', '-U', 'setuptools'],
            ['python/bin/python', 'bootstrap.py'],
            ['python/bin/python', 'alias.py'],
            addonsline,
        ]

    #cmd_line = ['PGPASSWORD=%s' % pw, 'psql', '-U', user, '-d', self.db_name, '< %s' % self.dpath]
    #print cmd_line
    #p = subprocess.Popen(cmd_line, shell=True, stdout=PIPE)
    #print p.communicate()
    for cmd_line in cmd_lines:
        if not cmd_line:
            continue
        print ' '.join(cmd_line)
        p = subprocess.Popen(cmd_line, stdout=PIPE)
        p.communicate()
        #os.system(' '.join(cmd_line))

    # now set the path in the odoorunner
    data = open('%s/bin/odoorunner.py' % PROJECT_HOME).read()
    data = data.replace('#--!/usr/bin/python--', '#!%s/bin/python' % PROJECT_HOME)
    f = open('%s/bin/odoorunner.py'  % PROJECT_HOME, 'w')
    f.write(data)
    f.close()
    # allways set svn:ignores
    handle_svn_ignores()

if __name__ == '__main__':
    usage = "dosetup.py -h for help on usage"
    parser = OptionParser(usage=usage)
    parser.add_option(
        "-i", "--ignores",
        action="store_true", dest="ignores", default=False,
        help = 'set svn:ignores'
    )
    parser.add_option(
        "-f", "--force",
        action="store_true", dest="force", default=False,
        help = 'overwrite existing login_info.cfg'
    )
    parser.add_option(
        "-n", "--noinit",
        action="store_true", dest="noinit", default=True,
        help = 'do not initialize virtual env'
    )
    parser.add_option(
        "-N", "--initonly",
        action="store_true", dest="initonly", default=False,
        help = 'do only initialize virtual env'
    )


    (opts, args) = parser.parse_args()
    main(opts) #opts.noinit, opts.initonly)
