#!/usr/bin/python
# -*- encoding: utf-8 -*-

FILES_TO_COPY = {
    # F = File
    # L = Link
    # D = Folder
    # R = copy and rename (sourcename, targetname)
    # T = Touch
    # '$FILE$' link to the source
    'project' : {
        'alias.py'          : 'F',
        'base_recipe.cfg'   : 'F',
        'bin'               : {
            # we want to link to the original dosetup.py so we can update it
            #'dosetup.py' : ('L','$FILE$'),
            'dosetup.py' : 'X',
            # python and pip are created whe running dosetup
            # we just want to link to them to be able to access them more easy
            'pip' : ('L', '../python/bin/pip'),
            'python' : ('L', '../python/bin/python'),
            # we want to link to the original update_local_db.py so we can update it
            #'update_local_db.py' : ('L','$FILE$'),
            'update_local_db.py' : 'X',
            'odoorunner.py' : 'X',
            '__init__.py' : 'T',
        },
        'bootstrap.py'      : 'F',
        'buildout.cfg'      : 'F',
        'install'           : {
            'INSTALL.txt' : 'F',
            'requirements.txt' : 'F',
        },
        'login_info.cfg.in' : 'F',
        'scripts'           : {
            'dodump.sh' : 'F',
            '__init__.py' : 'F',
            'README.txt' : 'F',
            'updatedb.sh' : 'F',
            # we want to link to the original update_local_db.py so we can update it
            #'update_local_db.py'  : ('L','$FILE$'),
            'update_local_db.py'  : 'F',
        },
        'Dockerfile' : 'F',
    },
    'project_home' : {
        'documents' : 'D',
        'README.txt' : 'T',
        'Python.gitignore' : ('R', '.gitignore')
    },
    'simple_copy' : {
        'base_recipe.cfg'   : 'F',
        'login_info.cfg.in' : 'F',
        'Python.gitignore' : ('R', '.gitignore'),
        'bin'               : {
            'dosetup.py' : 'X',
            'update_local_db.py' : 'X',
            'odoorunner.py' : 'X',
            '__init__.py' : 'T',
        },
    }

}
