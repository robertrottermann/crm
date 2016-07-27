#https://www.digitalocean.com/community/tutorials/how-to-set-up-a-private-docker-registry-on-ubuntu-14-04
from docker import Client
cli = Client(base_url='tcp://10.168.0.100:2375')
cli.containers()
