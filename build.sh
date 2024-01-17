#!/bin/bash

# Ensure safe execution
set -euo pipefail

echo "Building image..."
podman build -t nginx-build-image -f Containerfile .

echo "Building rpm..."
podman run \
    --name nginx-builder \
    --rm \
    -v $PWD/rpms/:/rpms:Z \
    localhost/nginx-build-image:latest \
    bash -c "rpmbuild -bb /root/rpmbuild/SPECS/nginx.spec && cp /root/rpmbuild/RPMS/x86_64/* /rpms/"
