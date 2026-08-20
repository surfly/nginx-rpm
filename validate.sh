#!/bin/bash

# Validates a built RPM before it is released: every module is present at the
# version nginx.spec pins, and resty.core actually loads. The WAF unit tests in
# cobro use a minimal config that never requires resty.core, so a mismatched
# lua-nginx-module / lua-resty-core pair passes them and kills nginx in prod.

set -euo pipefail

CALLER_PWD=$PWD
cd "$(dirname "$(readlink -f "$0")")"

RPM_PATH="${1:-}"
if [[ -n "$RPM_PATH" && "$RPM_PATH" != /* ]]; then
    RPM_PATH="$CALLER_PWD/$RPM_PATH"
fi
if [[ -z "$RPM_PATH" ]]; then
    # rpms/ is gitignored and accumulates, so refuse to guess between builds.
    shopt -s nullglob
    found=(rpms/*.rpm)
    if [[ ${#found[@]} -ne 1 ]]; then
        echo "found ${#found[@]} RPMs in rpms/, pass the one to validate" >&2
        exit 1
    fi
    RPM_PATH="${found[0]}"
fi
if [[ ! -f "$RPM_PATH" ]]; then
    echo "usage: $0 <path-to-rpm>" >&2
    exit 1
fi

RPM_DIR=$(cd "$(dirname "$RPM_PATH")" && pwd)
RPM_FILE=$(basename "$RPM_PATH")

FEDORA_VERSION=$(echo "$RPM_FILE" | grep -oE '\.fc[0-9]+\.' | tr -d '.fc' || true)
NGINX_VERSION=$(grep -m1 '^Version:' nginx.spec | awk '{print $2}' || true)
if [[ -z "$FEDORA_VERSION" || -z "$NGINX_VERSION" ]]; then
    echo "cannot read the Fedora version from $RPM_FILE or Version: from nginx.spec" >&2
    exit 1
fi

# The configure args embed each module's source directory, so its pinned version
# shows up in `nginx -V` output verbatim. Left of the colon is what appears there,
# right of it is the nginx.spec key holding the version.
MODULES=(
    "lua-nginx-module:lua_nginx_module_version"
    "ngx_devel_kit:ngx_devel_kit_version"
    "ngx_http_redis:ngx_http_redis_version"
    "headers-more-nginx-module:headers_more_version"
    "ModSecurity-nginx:modsecurity_nginx_version"
    "njs:njs_version"
)

EXPECTED=("nginx/$NGINX_VERSION")
for entry in "${MODULES[@]}"; do
    key=${entry##*:}
    version=$(grep -m1 -E "^%global ${key}[[:space:]]" nginx.spec | awk '{print $3}' || true)
    # An empty version would leave a bare "name-" prefix, which grep -F matches in
    # any nginx -V output -- the gate would pass on every build.
    if [[ -z "$version" ]]; then
        echo "nginx.spec has no %global $key" >&2
        exit 1
    fi
    EXPECTED+=("${entry%%:*}-$version")
done

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

# nginx -V only proves what ./configure was told, so load every shipped module to
# prove the .so files themselves are usable against this nginx.
moduledir="$(rpm --eval %{_libdir})/nginx/modules"
cat > /etc/nginx/nginx.conf <<CONF
load_module "$moduledir/ndk_http_module.so";
load_module "$moduledir/ngx_http_lua_module.so";
load_module "$moduledir/ngx_stream_module.so";
load_module "$moduledir/ngx_http_js_module.so";
load_module "$moduledir/ngx_stream_js_module.so";
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
