#!/bin/bash

# Ensure safe execution
set -euo pipefail

echo "Building image..."
podman build -t nginx-build-image-debug -f Containerfile.debug .

echo "Building rpm..."
podman run \
    --name nginx-builder \
    --rm \
    -it \
    -v $PWD/rpms/:/rpms:Z \
    -v $PWD/nginx.spec:/root/rpmbuild/SPECS/nginx.spec:Z \
    -v $PWD/nginx.service:/root/rpmbuild/SOURCES/nginx.service:Z \
    -v $PWD/nginx.logrotate:/root/rpmbuild/SOURCES/nginx.logrotate:Z \
    localhost/nginx-build-image:latest \
    bash -c "yum-builddep -y /root/rpmbuild/SPECS/nginx.spec && cd /root/rpmbuild/SPECS/ && bash"
