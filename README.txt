README.txt
----------

preparation:
------------
The following steps have to be executed once:

    install virtual env:
    --------------------
    In the the folder odoo_instances run the following commands:
        virtualenv python
        bin/pip install -r install/requirements.txt


    create localdata.py:
    --------------------
    To be able to run create_site or update_local_db you have to create and edit
    localdata.py. There is a template you can copy:
        cp localdata.py.in localdata.py


    create a config file with info about your project settings:
    -----------------------------------------------------------
    The scripts need to know where to write the new projects.
    run:
        bin/c -r
    This will ask some questions:
    1. path to the projects
        This is where new projects are created

    ..
    
now you are ready to go


create new site:
----------------
A new site is created using create_site.py
A shortcut exists with bin/c.sh
This script can create both local sites in the projects folder,
and also helps creating as a local docker container.
Both types get their data from ~/odoo_instances/SITENAME
Where SITENAME must exist in ~/odoo_instances/sites.py

to create a NEW site follow these steps:

1. add SITENAME to ~/odoo_instances/sites.py:
    bin/c.sh -n SITENAME --add-site

    This produces a new entry in ~/odoo_instances/sites.py which you have to
    edit to your needs.
2. create directories in ~/odoo_instances:
    you need the folowing directories in ~/odoo_instances
    SITENAME/addons
            /dump
            /etc
            /filestore
    the following command creates them:
    bin/c.sh -n SITENAME
3.

update local data:
------------------
