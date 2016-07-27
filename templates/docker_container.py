docker_template = """
docker run -p 127.0.0.1:%(odoo_port)s:8069 \
    -v %(remote_path)s/%(site_name)s/etc:/etc/odoo \
    -v %(remote_path)s/%(site_name)s/addons:/mnt/extra-addons \
    -v %(remote_path)s/%(site_name)s/dump:/mnt/dump \
    -v %(remote_path)s/%(site_name)s/filestore:/var/lib/odoo/filestore \
    -v %(remote_path)s/%(site_name)s/log:/var/log/odoo \
    --name %(container_name)s -d --link db:db -t %(odoo_image_version)s
"""
