#https://www.digitalocean.com/community/tutorials/how-to-set-up-a-private-docker-registry-on-ubuntu-14-04
from docker import Client
from config import ACT_USER
from update_local_db import DBUpdater
import sys
from utilities import get_remote_server_info, bcolors,  install_own_modules, get_module_obj

class dockerHandler(DBUpdater):
    master = '' # possible master site from which to copy 
    def __init__(self, opts, default_values, site_name, url='unix://var/run/docker.sock', use_tunnel=False):
        try:
            from docker import Client
        except ImportError:
            print '*' * 80
            print 'could not import docker'
            print 'please run bin/pip install -r install/requirements.txt'
            return
        super(dockerHandler, self).__init__(opts, default_values, site_name)
        self.site_name = site_name
        cli = self.default_values.get('docker_client')
        self.url = url
        if not cli:
            from docker import Client
            cli = Client(base_url=self.url)
            self.default_values['docker_client'] = cli
        self.update_container_info()
        self.docker_db_ip = cli.containers(filters = {'name' : 'db'})[0][u'NetworkSettings'][u'Networks']['bridge']['IPAddress']

    def update_docker_info(self, name, required=False, start=True):
        """
        update_docker_info checks if a docker exists and is started.
        If it does not exist and required is false, the container is created and started.
        If it does not exist and required is True, an error is thrown.
        If it does exist and is stoped and start is True, it is started.
        If it does exist and is stoped and start is False, nothing happens.
        
        In all cases, status info read from the docker engine is saved into the registry
        maintained in self.default_values['docker_registry']
        """
        registry = self.default_values.get('docker_registry', {})
        cli = self.default_values.get('docker_client')
        # check whether a container with the requested name exists.
        # similar to docker ps -a, we need to also consider the stoped containers
        exists  = cli.containers(filters={'name' : name}, all=1)
        if exists:
            # collect info on the container
            # this is equivalent to docker inspect name
            info = cli.inspect_container(name)
            if info:
                if info['State']['Status'] != 'running':
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
        else:
            if required:
                raise ValueError('required container:%s does not exist' % name)
        self.default_values['docker_registry'] = registry

    def update_container_info(self):
        """
        update_container_info tries to start all docker containers a site is associated with:
        The server where these dockers reside, depends on the options selected.
        It could be either localhost, or the remote host.
        Either two or three containers are handeled on each site:
        - db: this is the container containing the database. 
              it is only checkd for existence and started when stopped.
        - $DOCKERNAME: This is the docker that containes the actual site
              The value of $DOCKERNAME is read from the site info using the key 'docker'
        If the site is a slave, and a transfer from the master to the slave is requested:
        - $MASTER_DOCKERNAME: this is the container name of the master site as found in sites.py.
        """
        name = self.opts.name
        site_info = self.sites[name]
        docker = site_info.get('docker')
        if not docker or not docker.get('container_name'):
            print 'the site description for %s has no docker description or no container_name' % opts.name
            return
        # collect info on database container which allways is named 'db'
        self.update_docker_info('db', required=True)
        self.update_docker_info(docker['container_name'])
        # check whether we are a slave
        if self.opts.transferdocker and site_info.get('slave_info'):
            master_site = site_info.get('slave_info').get('master_site')
            if master_site:
                self.update_docker_info(master_site)
                

    def check_and_create_container(self):
        # if we land here docker info is acessible from sites.py
        name = self.opts.name
        container_name = self.sites[name]['docker']['container_name']
        odoo_port = self.sites[name]['docker']['odoo_port']
        if not self.default_values['docker_registry'].get(container_name):
            from templates.docker_container import docker_template
            docker_info = {
                'odoo_port' : odoo_port,
                'site_name' : name,
                'container_name' : container_name,
                'remote_path' : self.sites[name]['remote_server']['remote_path'],
                'odoo_image_version' : self.sites[name]['docker']['odoo_image_version'],
            }
            docker_template = docker_template % docker_info
            mp = self.default_values.get('docker_path_map')
            if mp and ACT_USER != 'root':
                try:
                    t, s = mp
                    docker_template = docker_template.replace(s, t)
                except:
                    pass
            self.run_commands([docker_template], user, pw)
            if self.opts.verbose:
                print docker_template
        else:
            if self.opts.verbose:
                print 'container %s allready running' % name
            
    def stop_container(self, name):
        self.default_values['docker_client'].stop(name)
        
    def doTransfer(self):
        super(dockerHandler, self).doTransfer()
        
    def checkImage(self, image_name):
        return self.default_values['docker_client'].images(image_name)

    def doUpdate(self, db_update=True, norefresh=None, names=[]):
        #self.update_container_info()
        # we need to learn what ip address the local docker db is using
        #if the container does not yet exists, we create them (master and slave)
        self.check_and_create_container()
        server_dic = get_remote_server_info(self.opts)
        # we have to decide, whether this is a local or remote
        remote_path = server_dic['remote_path']
        if not self.checkImage('dbdumper'):
            print bcolors.FAIL + 'the dbdumper image is not available. please create it first. \ninstrctions on how to do it , you find in %s/dumper' % self.default_values['sites_home'] + bcolors.ENDC
            return
            
        #mp = self.default_values.get('docker_path_map')
        #if mp and ACT_USER != 'root':
            #t, s = mp
            #remote_path = remote_path.replace(s, t)
        server_info = {
            'remote_url' : server_dic.get('remote_url'),
            'remote_user' : server_dic.get('remote_user'), #self.opts.dockerdbuser,
            'remote_data_dir' : remote_path,
            # pg_password is on local host. even when run remotely
            'pg_password' : self.opts.dockerdbpw,
            'user' : self.db_user,
            'pw' : self.db_password,
            
        }
        self._doUpdate(db_update, norefresh, self.opts.name, server_info)


    def install_own_modules(self, list_only=False, quiet=False):
        if list_only:
            return install_own_modules(self.opts, self.default_values, list_only, quiet)
        # get_module_obj
        docker_info = self.default_values['docker_registry'].get(self.site_name)
        db_info = self.default_values['docker_registry'].get(self.site_name)
        # docker_info['NetworkSettings']['IPAddress']
        ports = docker_info['NetworkSettings']['Ports'].get("8069/tcp") 
        dbhost = db_info['NetworkSettings']['IPAddress']
        info = {
            'rpchost' : 'localhost',
            'port' : ports[0].get("HostPort", '8069'),
            'rpcuser' : 'admin',
            'rpcpw' : self.sites[self.site_name]['odoo_admin_pw'],
            'dbuser' : 'odoo', # should be configurable
            'dbpw' : 'odoo', # should be configurable
            'dbhost' : dbhost,
            
        }
        return install_own_modules(self.opts, self.default_values, list_only, quiet, info)
    
