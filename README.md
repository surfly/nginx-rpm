nginx-lua-waf
================

## Description
This is a build of nginx which supports lua and modsecurity plugin (lua is a
dynamic module, loaded via `load_module`; consumers that don't need it, like
`xresproxy`, simply don't load it). It is intended
to be used as a reverse proxy with caching and WAF capabilities behind a load balancer.
It is built with `--with-http_ssl_module` so `proxy_ssl_*` directives work when acting
as an SSL client to an upstream (e.g. `xresproxy` fetching external HTTPS resources);
it does not terminate client-facing TLS itself, and ships no `http_v2`/`http_v3` modules
since nothing in our nginx configs uses them.

Features:
 - [luajit 2.1 from openresty](https://github.com/openresty/luajit2) is bundled with the build
 - [ngx_http_redis module](https://github.com/centminmod/ngx_http_redis/) - caching responses in Redis
 - [headers-more-nginx-module](https://github.com/openresty/headers-more-nginx-module) - for setting headers
 - [ModSecurity](https://github.com/owasp-modsecurity/ModSecurity-nginx) - waf capabilities
 - [njs](https://github.com/nginx/njs) - JavaScript scripting (ngx_http_js_module / ngx_stream_js_module), built as dynamic modules loaded via an absolute `load_module` path (see `mod-stream.conf` for the existing convention)

## Build instructions
Running `./build.sh` will output a new RPM file in the `rpms/` directory, and
`./validate.sh` checks it: every module is present at the version `nginx.spec`
pins, and `resty.core` loads (a mismatched lua-nginx-module / lua-resty-core pair
passes cobro's WAF unit tests but kills nginx in the prod config).

CI does both for `x86_64` and `aarch64` on every pull request, so a local build is
only needed to iterate on the spec. The build needs a host of the target
architecture — it is a native `rpmbuild`, not a cross-build.

## Development instructions
Running `./debug.sh` will build the container and start bash session inside it.
You can then run `rpmbuild -bb /root/rpmbuild/SPECS/nginx.spec` to build the RPM file.

## Release instructions
When RPM file is built, we upload it to github releases (for history) and to our
internal public storage.

- would be nice to create a repository for the RPMs
- it is not possible to use COPR, as the build requires absolute path to
  `LUAJIT_LIB` and `LUAJIT_INC` which is not possible to set in COPR because
  of permissions issues.

### Upload a new RPM to github releases:
Push a tag named `<Version>-<Release>` (matching `nginx.spec`) and CI builds both
architectures, validates them, and attaches them to that release — creating it if
it does not exist yet:

```bash
git tag 1.31.2-4 && git push origin 1.31.2-4
```

To attach an RPM by hand instead — a rebuild of an already-released tag, or an
architecture CI cannot reach:

```bash
grm release surfly/nginx-rpm -f rpms/<rpm-file> -t <version>

# Example:
# grm release surfly/nginx-rpm -f rpms/nginx-lua-waf-1.25.3-3.fc39.x86_64.rpm -t 1.25.3-3
```
