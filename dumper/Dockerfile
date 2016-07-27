# Dockerfile
FROM ubuntu:xenial


RUN apt-get update && \
    apt-get install postgresql-client vim python -y


ENTRYPOINT ["/usr/bin/python", "/mnt/sites/dumper/dumper.py"]
