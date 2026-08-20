#!/bin/bash

# Validates a built RPM before it is released: every module is present at the
# version nginx.spec pins, and resty.core actually loads. The WAF unit tests in
# cobro use a minimal config that never requires resty.core, so a mismatched
# lua-nginx-module / lua-resty-core pair passes them and kills nginx in prod.

set -euo pipefail

RPM_PATH="${1:-}"
if [[ -z "$RPM_PATH" ]]; then
    RPM_PATH=$(ls -1 rpms/*.rpm 2>/dev/null | head -n1 || true)
fi
if [[ -z "$RPM_PATH" || ! -f "$RPM_PATH" ]]; then
    echo "usage: $0 <path-to-rpm>   (default: the first file in rpms/)" >&2
    exit 1
fi

RPM_DIR=$(cd "$(dirname "$RPM_PATH")" && pwd)
RPM_FILE=$(basename "$RPM_PATH")

spec_global() {
    grep -m1 "^%global $1 " nginx.spec | awk '{print $3}'
}

FEDORA_VERSION=$(echo "$RPM_FILE" | grep -oE '\.fc[0-9]+\.' | tr -d '.fc')
NGINX_VERSION=$(grep -m1 '^Version:' nginx.spec | awk '{print $2}')

# The configure args embed each module's source directory, so its pinned version
# shows up in `nginx -V` output verbatim.
EXPECTED=(
    "nginx/$NGINX_VERSION"
    "lua-nginx-module-$(spec_global lua_nginx_module_version)"
    "ngx_devel_kit-$(spec_global ngx_devel_kit_version)"
    "ngx_http_redis-$(spec_global ngx_http_redis_version)"
    "headers-more-nginx-module-$(spec_global headers_more_version)"
    "ModSecurity-nginx-$(spec_global modsecurity_nginx_version)"
    "njs-$(spec_global njs_version)"
)

echo "Validating $RPM_FILE against fedora:$FEDORA_VERSION"

LOG=$(mktemp)
trap 'rm -f "$LOG"' EXIT

podman run --rm -i \
    -v "$RPM_DIR":/rpms:Z \
    -e RPM_FILE="$RPM_FILE" \
    -e EXPECTED="${EXPECTED[*]}" \
    "quay.io/fedora/fedora:$FEDORA_VERSION" bash -s <<'CONTAINER' | tee "$LOG"
set -euo pipefail

dnf install -y "/rpms/$RPM_FILE" > /dev/null

echo "--- nginx -V ---"
nginx -V 2>&1 | tee /tmp/nginx-V

missing=0
for want in $EXPECTED; do
    if grep -qF "$want" /tmp/nginx-V; then
        echo "ok      $want"
    else
        echo "MISSING $want"
        missing=1
    fi
done
if [[ $missing -ne 0 ]]; then
    echo "nginx -V does not match the versions pinned in nginx.spec" >&2
    exit 1
fi

moduledir="$(rpm --eval %{_libdir})/nginx/modules"
cat > /etc/nginx/nginx.conf <<CONF
load_module "$moduledir/ndk_http_module.so";
load_module "$moduledir/ngx_http_lua_module.so";
events {}
http {
    lua_package_path "/usr/local/lib/lua/?.lua;;";
    init_by_lua_block { require "resty.core" }
    server { listen 8080; }
}
CONF

echo "--- resty.core gate ---"
nginx -t

echo VALIDATED
CONTAINER

# Drop the -i above and the container's bash reads EOF, runs nothing and exits 0,
# so the sentinel is what proves the checks ran -- not the exit code.
grep -qx VALIDATED "$LOG"

echo "OK: $RPM_FILE"
