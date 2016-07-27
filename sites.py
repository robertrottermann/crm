#!/usr/bin/python
# -*- encoding: utf-8 -*-

# sites.py lists all sites
# -------------------------------------------------------------
# the marker is used to place a new site when the file is updated
# -------------------------------------------------------------
MARKER = '# ---------------- marker ----------------'
# -------------------------------------------------------------
# add new sites to SITES_G
# local sites should be added to sites_local.py
# use sites_local.py.in as template
# -------------------------------------------------------------
SITES_G = {
    "afbs" : {

        'servername' : 'afbs',
        'odoo_admin_pw' : '',
        'odoo_version' : '9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'afbs',
        'pg_password' : 'odoo',
        'email_user_incomming' : 'mailhandler@afbs.ch',
        'email_pw_incomming' : '',
        'email_user_outgoing' : 'mailhandler@afbs.ch',
        'email_pw_outgoing' : '',
        'remote_server' : {
            'remote_url'    : '82.220.39.73', # elsbeth
            'remote_path'   : '/root/odoo_instances',
            'remote_user'   : 'root',
        },
        'docker' : {
            'odoo_image_version': 'odoo:9.0',
            'container_name'    : 'afbs',
            'odoo_port'         : '8070',
        },
        'apache' : {
            'vservername'   : 'www.afbs.ch',
            'vserveraliases': ['afbs.ch','afbs.redcor.ch',],
        },
        # odoo_addons allow to install odoo base tools
        'odoo_addons' : [
            'crm',
            'invoicing',
            'online events',
            'dashboards',
            'slides',
            'calendar',
            'discuss',
            'projects',
            'accounting and finance ',
            'inventory management',
            'issue tracking',
            'purchase management',
            'website builder',
            'survey',
            'mass mailing campaigns',
            'blogs',
        ],
        'addons' : [
            {
                'type' : 'git',
                'url' : 'https://github.com/robertrottermann/crm.git',
                'branch' : '9.0',
                'subdir' : 'mass_mailing_partner',
                'group'  : 'crm_oca',
                'add_path'  : 'crm_oca',
                'name' : 'mass_mailing_partner',
            },
            {
                'type'      : 'git',
                'url'       : 'ssh://git@gitlab.redcor.ch:10022/afbs/afbs_import_mapper.git',
                'group'     : 'mapper',
            },
            {
                'type' : 'git',
                'url' : 'https://github.com/OCA/partner-contact.git',
                'branch' : '9.0',
                'group'  : 'partner-contact',
                'add_path' : 'partner-contact',
                'subdir' : 'partner_firstname',
                'name'   : 'partner_firstname',
            },
            {
                'type' : 'git',
                'url' : 'ssh://git@gitlab.redcor.ch:10022/afbs/afbs_extra_data.git',
                'group'  : 'afbs_extra_data',
                'branch' : '9.0',
            },
            {
                'type' : 'git',
                'url' : 'ssh://git@gitlab.redcor.ch:10022/afbs/afbs_membership.git',
                'group'  : 'afbs_membership',
                'branch' : '9.0',
            },
            {
                'type' : 'git',
                'url' : 'ssh://git@gitlab.redcor.ch:10022/yaseenshareef91/cms-dms.git',
                'group'  : 'cms-dms',
                'add_path' : 'cms-dms',
            },
            {
                'type' : 'git',
                'url' : 'ssh://git@gitlab.redcor.ch:10022/afbs/afbs_workgroups.git',
                'group'  : 'afbs_workgroups',
                'branch' : '9.0',
            },
            {
                'type' : 'git',
                'url' : 'https://github.com/robertrottermann/Therp-Addons.git',
                'group'  : 'therp-addons',
                'add_path'  : 'therp-addons',
                'branch' : '8.0',
                'name' : 'override_mail_recipients',
            },
            {
                'type' : 'git',
                'url' : 'ssh://git@gitlab.redcor.ch:10022/open-source/mail_thread_fetchall.git',
                'group'  : 'mail_thread_fetchall',
            },
            {
                'type' : 'git',
                'url' : 'ssh://git@gitlab.redcor.ch:10022/afbs/afbs_dashboard.git',
                'group'  : 'afbs_dashboard',
            },
            {
                'type'      : 'git',
                'url'       : 'ssh://git@gitlab.redcor.ch:10022/afbs/afbs-website.git',
                'group'     : 'afbs_website',
                'name'      : 'afbs_website',
            },
        ],
        'skip' : {
            #'addons' : ['cms-dms']
        },
        'pip' : [
        ],
    },
    "afbschweiz" : {
        'site_name' : 'afbschweiz',
        'servername' : 'afbschweiz',
        'odoo_admin_pw' : '',
        'odoo_version' : '9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'afbschweiz',
        'pg_password' : 'odoo',
        'email_user_incomming' : 'mailhandler@afbs.ch',
        'email_pw_incomming' : '',
        'email_user_outgoing' : 'mailhandler@afbs.ch',
        'email_pw_outgoing' : '',
        'inherit'   : 'afbs',
        'docker' : {
            'container_name'    : 'afbschweiz',
            'odoo_port'         : '8072',
        },
        'apache' : {
            'vservername'   : 'www.afbs.ch',
            'vserveraliases': ['afbs.ch','afbs.redcor.ch',],
        },
        'skip' : {
            'addons' : ['cms-dms', 'afbs_workgroups']
        },
    },
    "afbstest" : {
        'site_name' : 'afbstest',
        'servername' : 'afbstest',
        'odoo_admin_pw' : '',
        'odoo_version' : '9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'afbstest',
        'pg_password' : 'odoo',
        'email_user_incomming' : 'mailhandler@afbs.ch',
        'email_pw_incomming' : '',
        'email_user_outgoing' : 'mailhandler@afbs.ch',
        'email_pw_outgoing' : '',
        'inherit'   : 'afbs',
        'docker' : {
            'container_name'    : 'afbstest',
            'odoo_port'         : '8071',
        },
        'apache' : {
            'vservername'   : 'test.afbs.ch',
            'vserveraliases': [],
        },
        'slave_info' : {
            # master_site ist the name of the mastersite
            # this must be a site in sites.py
            "master_site" : 'afbschweiz',
            # master_domain is the domain from which the master is copied
            "master_domain" : 'localhost',

        },
        'skip' : {
            #'addons' : ['cms-dms']
        }
    },
    "breitschtraeff9" : {
        'site_name' : 'breitschtraeff9',
        'servername' : 'breitschtraeff9',
        'remote_url' : '144.76.184.20',
        'remote_path' : '/root/odoo_instances',
        'remote_user' : 'root',
        'odoo_port'   : '8077',
        'odoo_version' : '9.0',
        'odoo_image_version' : 'odoo:9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'breitschtraeff9',
        'pg_password' : 'odoo',
        'email_user_incomming' : 'helpdesk@go2breitsch.ch',
        'email_user_outgoing' : 'helpdesk@go2breitsch.ch',
        'addons' : [
            {
                #git https://github.com/tobwetzel/partner_naming.git breitschtraeff9_addons/ master group=breitschtraeff9_addons/partner_naming
                'type' : 'git',
                'url' : 'https://github.com/tobwetzel/partner_naming.git',
                'group' : 'partner_naming',
            },
            {
                #git ssh://git@gitlab.redcor.ch:10022/hilar/issue_to_event.git breitschtraeff9_addons/issue_to_event 9.0
                'type' : 'git',
                'url' : 'ssh://git@gitlab.redcor.ch:10022/hilar/issue_to_event.git',
                'branch' : '9.0',
                'group' : 'issue_to_event',
                'add_path'   : 'issue_to_event',
            },
            {
                #git ssh://git@gitlab.redcor.ch:10022/l10n_ch/l10n_ch_payment_fix_pos.git breitschtraeff9_addons/l10n_ch_payment_fix_pos
                'type' : 'git',
                'url' : 'https://github.com/prakashatredcor/l10n-switzerland.git',
                'branch' : '9.0',
                'group' : 'l10n-switzerland_oca',
                'add_path' : 'l10n-switzerland_oca',
            },
            {
                #git ssh://git@gitlab.redcor.ch:10022/l10n_ch/l10n_ch_payment_fix_pos.git breitschtraeff9_addons/l10n_ch_payment_fix_pos
                'type' : 'git',
                'url' : 'ssh://git@gitlab.redcor.ch:10022/l10n_ch/l10n_ch_payment_fix_pos.git',
                'group' : 'l10n_ch_payment_fix_pos',
            },
        ],
        'pip' : [
            'passlib',
        ],
    },
    "docmarolf" : {
        'db_name': 'docmarolf',
        'email_user_incomming': 'cardiolog@docmarolf.ch',
        'email_user_outgoing': 'cardiocare@docmarolf.ch',
        'odoo_image_version': 'odoo:9.0',
        'odoo_version': '9.0',
        'pg_password': 'odoo',
        'servername': 'docmarolf',
        'site_name': 'docmarolf',
        'smtp_server': 'mail.redcor.ch',
        'remote_server' : {
            'remote_url'    : '144.76.184.20', # frieda
            'remote_path'   : '/root/odoo_instances',
            'remote_user'   : 'root',
        },
        'docker' : {
            'odoo_image_version': 'odoo:9.0',
            'container_name'    : 'docmarolf',
            'odoo_port'         : '8075',
        },
        'apache' : {
            'vservername'   : 'www.docmarolf.ch',
            'vserveraliases': ['docmarolf.ch',],
        },
        'addons' : [
            #  {
            #      'type' : 'git',
            #      'url' : 'ssh://git@gitlab.redcor.ch:10022/agenda2go/docmarolf_calendar.git',
            #      'target' : 'docmarolf_calendar',
            #      #'group' : 'docmarolf',
            #      'group' : 'docmarolf_addons/docmarolf_calendar',
            #  },

            {
                'type' : 'git',
                'url' : 'ssh://git@gitlab.redcor.ch:10022/agenda2go/docmarolf_calendar.git',
                #'target' : 'docmarolf_addons',
                'group' : 'docmarolf_calendar',
            },
        ],
        'pip' : [
            'pdfkit',
            'tzlocal',
        ],
    },
    "docmarolf2" : {
        'site_name'     : 'docmarolf2',
        'servername'    : 'docmarolf2',
        'odoo_admin_pw' : '',
        'odoo_version'  : '9.0',
        'smtp_server'   : 'mail.redcor.ch',
        'db_name'       : 'docmarolf2',
        'pg_password'   : 'odoo',
        'email_user_incomming'  : '',
        'email_pw_incomming'    : '',
        'email_user_outgoing'   : '',
        'email_pw_outgoing'     : '',
        'remote_server' : {
            'remote_url'    : '144.76.184.20', #frieda
            'remote_path'   : '/root/odoo_instances',
            'remote_user'   : 'root',
        },
        'docker' : {
            'odoo_image_version': 'odoo:9.0',
            'container_name'    : 'docmarolf2',
            'odoo_port'         : '8079',
        },
        'apache' : {
            'vservername'   : 'new.docmarolf.ch',
            'vserveraliases': ['docmarolf.ch',],
            'odoo_port'     : '79',
        },
        'inherit' : 'docmarolf',
    },
    "ecassoc" : {
        'site_name' : 'ecassoc',
        'servername' : 'ecassoc',
        'remote_url' : '144.76.184.20',
        'remote_path' : '/root/odoo_instances',
        'remote_user' : 'root',
        'odoo_port'   : '8074',
        'odoo_version' : '9.0',
        'odoo_image_version' : 'odoo:9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'ecassoc',
        'pg_password' : 'odoo',
        'email_user_incomming' : 'ecasincomming@redcor.ch',
        'email_user_outgoing' : 'ecassoc@redcor.ch',
        'addons' : [
            {},
        ],
        'pip' : [
        ],
    },
    "harito" : {
        'site_name' : 'harito',
        'servername' : 'harito',
        'remote_url' : '144.76.184.20',
        'remote_path' : '/root/odoo_instances',
        'remote_user' : 'root',
        'odoo_port'   : '8071',
        'odoo_version' : '9.0',
        'odoo_image_version' : 'odoo:9.0',
        'smtp_server' : 'smtp.gmail.com',
        'db_name' : 'harito',
        'pg_password' : 'odoo',
        'email_user_incomming' : 'harito@redcor.ch',
        'email_user_outgoing' : '',
        'addons' : [
            {},
        ],
        'pip' : [
        ],
    },
    "redcorkmu" : {
        'site_name' : 'redcorkmu',
        'servername' : 'redcorkmu',
        'remote_url' : '144.76.184.20',
        'remote_path' : '/root/odoo_instances',
        'remote_user' : 'root',
        'odoo_port'   : '8073',
        'odoo_version' : '9.0',
        'odoo_image_version' : 'odoo:9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'redcorkmu',
        'pg_password' : 'odoo',
        'email_user_incomming' : 'helpdesk@redcor.ch',
        'email_user_outgoing' : 'redcorkmu@redcor.ch',
    },
    "eplusp" : {
        'site_name' : 'eplusp',
        'servername' : 'eplusp',
        'remote_url' : '144.76.184.20',
        'remote_path' : '/root/odoo_instances',
        'remote_user' : 'root',
        'odoo_port'   : '8076',
        'odoo_version' : '9.0',
        'odoo_image_version' : 'odoo:9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'eplus',
        'pg_password' : 'odoo',
        'email_user_incomming' : 'eplusp@redcor.ch',
        'email_user_outgoing' : '',
        'addons' : [
            {},
        ],
        'pip' : [
        ],
    },
    "key2gont" : {
        'site_name' : 'key2gont',
        'servername' : 'key2gont',
        'remote_url' : '144.76.184.20',
        'remote_path' : '/root/odoo_instances',
        'remote_user' : 'root',
        'odoo_port'   : '??',
        'odoo_version' : '9.0',
        'odoo_image_version' : 'odoo:9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'key2gont',
        'pg_password' : 'odoo',
        'email_user_incomming' : '',
        'email_user_outgoing' : '',
        'addons' : [
            {},
        ],
        'pip' : [
        ],
    },
    "rederpdemo" : {
        'site_name' : 'rederpdemo',
        'servername' : 'rederpdemo',
        'remote_url' : '144.76.184.20',
        'remote_path' : '/root/odoo_instances',
        'remote_user' : 'root',
        'odoo_port'   : '8078',
        'odoo_version' : '9.0',
        'odoo_image_version' : 'odoo:9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'rederpdemo',
        'pg_password' : 'odoo',
        'email_user_incomming' : 'helpdesk@erpdemo.redcor.ch',
        'email_user_outgoing' : 'helpdesk@erpdemo.redcor.ch',
        'addons' : [
            {},
        ],
        'pip' : [
        ],
    },
    "team2go" : {
        'site_name' : 'team2go',
        'servername' : 'team2go',
        'remote_url' : '144.76.184.20',
        'remote_path' : '/root/odoo_instances',
        'remote_user' : 'root',
        'odoo_port'   : '??',
        'odoo_admin_pw' : '',
        'odoo_version' : '9.0',
        'odoo_image_version' : 'odoo:9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'team2go',
        'pg_password' : 'odoo',
        'email_user_incomming' : '',
        'email_pw_incomming' : '',
        'email_user_outgoing' : '',
        'email_pw_outgoing' : '',
        'addons' : [
            {},
        ],
        'pip' : [
        ],
    },
    "horti2go" : {
        'site_name' : 'horti2go',
        'servername' : 'horti2go',
        'remote_url' : '144.76.184.20',
        'remote_path' : '/root/odoo_instances',
        'remote_user' : 'root',
        'odoo_port'   : '??',
        'odoo_admin_pw' : '',
        'odoo_version' : '9.0',
        'odoo_image_version' : 'odoo:9.0',
        'smtp_server' : 'mail.redcor.ch',
        'db_name' : 'horti2go',
        'pg_password' : 'odoo',
        'email_user_incomming' : '',
        'email_pw_incomming' : '',
        'email_user_outgoing' : '',
        'email_pw_outgoing' : '',
    },
    "roduit" : {
        'site_name'     : 'roduit',
        'servername'    : 'roduit',
        'odoo_admin_pw' : '',
        'odoo_version'  : '9.0',
        'smtp_server'   : 'mail.redcor.ch',
        'db_name'       : 'roduit',
        'pg_password'   : 'odoo',
        'email_user_incomming'  : '',
        'email_pw_incomming'    : '',
        'email_user_outgoing'   : '',
        'email_pw_outgoing'     : '',
        'remote_server' : {
            'remote_url'    : '46.4.89.241', #salome
            'remote_path'   : '/root/odoo_instances',
            'remote_user'   : 'root',
        },
        'docker' : {
            'odoo_image_version': 'odoo:9.0',
            'container_name'    : 'roduit',
            'odoo_port'     : '8070',
        },
        'apache' : {
            'vservername'   : 'www.roduit.ch',
            'vserveraliases': ['roduit.ch',],
        },
        'odoo_addons' : [
            'website builder',
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
                ## subdir is used to only use a sudirectory from the repository
                #'subdir : 'somesubdir',
            },
        ],
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
    "assocmanagement" : {
        'site_name'     : 'assocmanagement',
        'servername'    : 'assocmanagement',
        'odoo_admin_pw' : '',
        'odoo_version'  : '9.0',
        'smtp_server'   : 'mail.redcor.ch',
        'db_name'       : 'assocmanagement',
        'pg_password'   : 'odoo',
        'email_user_incomming'  : '',
        'email_pw_incomming'    : '',
        'email_user_outgoing'   : '',
        'email_pw_outgoing'     : '',
        'remote_server' : {
            'remote_url'    : '144.76.184.20', #frieda, please adapt
            'remote_path'   : '/root/odoo_instances',
            'remote_user'   : 'root',
        },
        'docker' : {
            'odoo_image_version': 'odoo:9.0',
            'container_name'    : 'assocmanagement',
        },
        'apache' : {
            'vservername'   : 'www.assocmanagement.ch',
            'vserveraliases': ['assocmanagement.ch',],
            'odoo_port'     : '??',
        },
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
    "altgewohnt" : {
        'site_name'     : 'altgewohnt',
        'servername'    : 'altgewohnt',
        'odoo_admin_pw' : '',
        'odoo_version'  : '9.0',
        'smtp_server'   : 'mail.redcor.ch',
        'db_name'       : 'altgewohnt',
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
            'container_name'    : 'altgewohnt',
        },
        'apache' : {
            'vservername'   : 'www.altgewohnt.ch',
            'vserveraliases': ['altgewohnt.ch',],
            'odoo_port'     : '??',
        },
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
# ---------------- marker ----------------




}

# -------------------------------------------------------------
# leave below lines untouched
# -------------------------------------------------------------
SITES_L = {}
import sys
import os
SITES_HOME =  os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
sys.path.insert(0, SITES_HOME)
try:
    from sites_local import SITES_L
    # -------------------------------------------------------------
    # test code from prakash to set the local sites value to true
    #------------------------------------------------------------
    for key in SITES_L.keys():
        SITES_L[key]['is_local'] = True
except ImportError:
    pass

SITES = {}
SITES.update(SITES_G)
SITES.update(SITES_L)

# -------------------------------------------------------------
# merge passwords
# -------------------------------------------------------------
DEFAULT_PWS = {
    'odoo_admin_pw' : '',
    'email_pw_incomming' : '',
    'email_pw_outgoing' : '',
}
# read passwords
SITES_PW = {}
try:
    from sites_pw import SITES_PW
except ImportError:
    pass
# merge them
for key in SITES.keys():
    kDic = SITES_PW.get(key, DEFAULT_PWS)
    for k in DEFAULT_PWS.keys():
        SITES[key][k] = kDic.get(k, '')
