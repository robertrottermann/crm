#https://www.digitalocean.com/community/tutorials/how-to-set-up-a-private-docker-registry-on-ubuntu-14-04
from docker import Client
from config import ACT_USER
from update_local_db import DBUpdater
import sys
from utilities import get_remote_server_info

class dockerHandler(DBUpdater):
    master = '' # possible master site from which to copy 
    def __init__(self, opts, default_values, site_name, url='unix://var/run/docker.sock', ):
        super(dockerHandler, self).__init__(opts, default_values, site_name)
        cli = self.default_values.get('docker_client')
        self.url = url
        if not cli:
            from docker import Client
            cli = Client(base_url=self.url)
            self.default_values['docker_client'] = cli
        self.update_container_info()
        self.docker_db_ip = cli.containers(filters = {'name' : 'db'})[0][u'NetworkSettings'][u'Networks']['bridge']['IPAddress']

    def update_docker_info(self, name, required=False, start=True):
        registry = self.default_values.get('docker_registry', {})
        cli = self.default_values.get('docker_client')
        exists  = cli.containers(filters={'name' : name}, all=1)
        if exists:
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
        sys.path.insert(0, '..')
        try:
            from docker import Client
        except ImportError:
            print '*' * 80
            print 'could not import docker'
            print 'please run bin/pip install -r install/requirements.txt'
            return
        name = self.opts.name
        site_info = self.sites[name]
        docker = site_info.get('docker')
        if not docker or not docker.get('container_name'):
            print 'the site description for %s has no docker description or no container_name' % opts.name
            return
        # collect info on database container which allways is named 'db'
        self.update_docker_info('db', required=True)
        self.update_docker_info(docker['container_name'])
        #check whether we are a slave
        if site_info.get('slave_info'):
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
            self.run_commands([docker_template])
            if self.opts.verbose:
                print docker_template
        else:
            if self.opts.verbose:
                print 'container %s allready running' % name
            
    def stop_container(self, name):
        self.default_values['docker_client'].stop(name)
        
    def doTransfer(self):
        super(dockerHandler, self).doTransfer()

    def doUpdate(self, db_update=True, norefresh=None, names=[]):
        #self.update_container_info()
        # we need to learn what ip address the local docker db is using
        #if the container does not yet exists, we create them (master and slave)
        self.check_and_create_container()
        server_dic = get_remote_server_info(self.opts)
        server_info = {
            'remote_url' : server_dic.get('remote_url'),
            'remote_user' : self.opts.dockerdbuser,
            'remote_data_dir' : self.sites_home,
            # pg_password is on local host. even when run remotely
            'pg_password' : self.opts.dockerdbpw,
        }
        self._doUpdate(db_update, norefresh, self.opts.name, server_info)

        