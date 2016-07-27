
    "%(site_name)s" : {
        'site_name'     : '%(site_name)s',
        'servername'    : '%(site_name)s',
        'odoo_admin_pw' : '',
        'odoo_version'  : '9.0',
        'smtp_server'   : 'mail.redcor.ch',
        'db_name'       : '%(site_name)s',
        'pg_password'   : 'odoo',
        'email_user_incomming'  : '',
        'email_pw_incomming'    : '',
        'email_user_outgoing'   : '',
        'email_pw_outgoing'     : '',
        # inherits tells from what other site we want to inherit values
        'inherit'   : '',
        'remote_server' : {
            'remote_url'    : '144.76.184.20', #frieda, please adapt
            'remote_path'   : '/root/odoo_instances',
            'remote_user'   : 'root',
        },
        'docker' : {
            'odoo_image_version': 'odoo:9.0',
            'container_name'    : '%(site_name)s',
            'odoo_port'     : '??',
        },
        'apache' : {
            'vservername'   : 'www.%(site_name)s.ch',
            'vserveraliases': ['%(site_name)s.ch',],
        },
        # odoo_addons allow to install odoo base tools
        'odoo_addons' : [
            #'website builder',
            #'crm',
        ],
        'addons' : [
            {
                # ***********************************
                # please clean out lines not needed !
                # ***********************************
                ## what type is the repository
                #'type' : 'git',
                ## what is the url to the repository
                #'url' : 'ssh://git@gitlab.redcor.ch:10022/agenda2go/docmarolf_calendar.git',
                ## branch is the repositories branch to be used. default 'master'
                #'branch' : 'branch.xx',
                ## what is the target (subdirectory) within the addons folder
                #'target' : 'docmarolf_calendar',
                ## group what group should be created within the target directory.
                ## see http://docs.anybox.fr/anybox.recipe.odoo/1.9.1/configuration.html#addons
                #'group' : 'somegroup',
                ## add_path is added to the addon path
                ## it is needed in the case when group of modules are added under a group
                #'add_path : 'somesubdir',
            },
        ],
        'skip' : {
            # the addons to skip when installing
            # the name is looko up in the addon stanza in the following sequence:
            # - name
            # - add_path
            # - group
            'addons' : [],
        },
        'pip' : [
        ],
        # slave info: is this site slave of a master site from which it will be updated
        'slave_info' : {
            # # master_site ist the name of the mastersite
            # # this must be a site in sites.py
            # "master_site" : '',
            # # master_domain is the domain from which the master is copied
            # "master_domain" : 'localhost',
        }
    },
%(marker)s
