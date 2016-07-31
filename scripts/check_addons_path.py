#!bin/python
# -*- encoding: utf-8 -*-
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def check_addons_paths(cfg_path, path_mapping=[], verbose=False, create=False):
    # path is a path to a openerp.conf file or to a folder containing it
    if os.path.exists(cfg_path) and os.path.isdir(cfg_path):
        cfg_path = '%s/openerp.cfg' % cfg_path
    if not os.path.exists(cfg_path):
        print bcolors.FAIL + '%s can not be accessed' % cfg_path + bcolors.ENDC
        return
    addons = [
        a.strip() for a in [
            l.split('=')[-1].strip() for l in open(cfg_path).read().split('\n') if l.find('addons_path') > -1][0].split(',')]
    result = []
    for addon in addons:
        if verbose:
            print addon
        if path_mapping:
            # odoo running in a docker, has an other addon origin
            m1, m2 = path_mapping
            addon = addon.replace(m1, m2)
        if not os.path.exists(addon):
            result.append(bcolors.FAIL + '%s does not exist' % addon + bcolors.ENDC)
            if create:
                try:
                    os.mkdir(addon)
                    result.append(bcolors.WARNING + '%s created' % addon + bcolors.ENDC)
                except:
                    result.append(bcolors.FAIL + '%s could not be created' % addon + bcolors.ENDC)
    if result:
        print '\n'.join(result)

if __name__ == '__main__':
    check_addons_paths('/home/robert/projects/afbstest/afbstest/etc', verbose=True)
    mapping = ('/mnt/extra-addons', '/home/robert/odoo_instances')
    check_addons_paths('/home/robert/odoo_instances/afbstest/etc/openerp-server.conf', verbose=True, path_mapping=mapping)
