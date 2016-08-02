create dbdumper image:
----------------------
    to be able to do transfer data to a databse within docker, we need a dbdumer Image
    this can be created as follows:

      cd dumper
      # make sure that the ubuntu version used in the dockerfile
      # employs the same postgres version, as the one running in the container named 'db'
      docker build  -t dbdumper . # this creates the image
      test it:
          docker run -v /root/odoo_instances:/mnt/sites --rm=true --link db:db -it dbdumper -h
