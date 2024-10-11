nginx-lua-waf
================

## Description
This is a build of nginx which supports lua and modesecurity plugin. It is intended
to be used as a reverse proxy with caching and WAF capabilities behind a load balancer
(it is currently built without SSL support).

Features:
 - [luajit 2.1 from openresty](https://github.com/openresty/luajit2) is bundled with the build
 - [ngx_http_redis module](https://github.com/centminmod/ngx_http_redis/) - caching responses in Redis
 - [headers-more-nginx-module](https://github.com/openresty/headers-more-nginx-module) - for setting headers
 - [ModSecurity](https://github.com/owasp-modsecurity/ModSecurity-nginx) - waf capabilities

## Build instructions
Running `./build.sh` will output a new RPM file in the `rpms/` directory.

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
```bash
grm release surfly/nginx-rpm -f rpms/<rpm-file> -t <version>

# Example:
# grm release surfly/nginx-rpm -f rpms/nginx-lua-waf-1.25.3-3.fc39.x86_64.rpm -t 1.25.3-3
```
