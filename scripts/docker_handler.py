#https://www.digitalocean.com/community/tutorials/how-to-set-up-a-private-docker-registry-on-ubuntu-14-04
from docker import Client
from localdata import DB_USER, DB_PASSWORD
from update_local_db import DBUpdater

class dockerHandler(DBUpdater):
    def __init__(self, opts, default_values, site_name, url='unix://var/run/docker.sock', ):
        super(dockerHandler, self).__init__(opts, default_values, site_name)
        cli = self.default_values.get('docker_client')
        self.url = url
        if not cli:
            from docker import Client
            cli = Client(base_url=self.url)
            self.default_values['docker_client'] = cli

    def update_docker_info(self, name, required=False, start=True):
        registry = self.default_values.get('docker_registry', {})
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

    def update_container_info(self):
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
        self.update_docker_info(default_values, 'db', required=True)
        self.update_docker_info(default_values, docker['container_name'])
        #check whether we are a slave
        if site_info.get('slave_info'):
            master_site = site_info.get('slave_info').get('master_site')
            if master_site:
                self.update_docker_info(default_values, master_site)

    def check_and_create_container(self):
        self.update_container_info()
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
            self.run_commands(opts, [docker_template])
            print docker_template
        else:
            print 'container %s allready running' % name
