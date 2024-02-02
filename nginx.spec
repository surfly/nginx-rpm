%global nginx_user nginx
%global nginx_moduledir %{_libdir}/nginx/modules
%global nginx_moduleconfdir %{_datadir}/nginx/modules
%global nginx_srcdir %{_usrsrc}/%{name}-%{version}-%{release}
%global lua_lib /usr/lib
%global lua_local_lib /usr/local/lib/lua
%global lua_nginx_module_version 0.10.26
%global lua_resty_core_version 0.1.28
%global lua_resty_lrucache_version 0.13
%global ngx_devel_kit_version 0.3.3
%global luajit2_version 2.1-20231117
%global ngx_http_redis_version 0.4.1-cmm
%global headers_more_version 0.37
%global modsecurity_nginx_version 1.0.3

# By default downloading of sources is disabled
%undefine _disable_source_fetch

Name: nginx-lua-waf
Summary: High performance web server nginx with lua and modsecurity plugins
Version: 1.25.3
Release: 3%{?dist}
Conflicts: nginx nginx-mimetypes nginx-core luajit

Source0: https://nginx.org/download/nginx-%{version}.tar.gz
Source1: nginx.service
Source2: nginx.logrotate
Source3: nginx.conf
Source100: https://github.com/openresty/lua-nginx-module/archive/refs/tags/v%{lua_nginx_module_version}.tar.gz
Source101: https://github.com/openresty/luajit2/archive/refs/tags/v%{luajit2_version}.tar.gz
Source102: https://github.com/vision5/ngx_devel_kit/archive/refs/tags/v%{ngx_devel_kit_version}.tar.gz
Source103: https://github.com/openresty/lua-resty-core/archive/refs/tags/v%{lua_resty_core_version}.tar.gz
Source104: https://github.com/openresty/lua-resty-lrucache/archive/refs/tags/v%{lua_resty_lrucache_version}.tar.gz
Source105: https://github.com/centminmod/ngx_http_redis/archive/refs/tags/%{ngx_http_redis_version}.tar.gz
Source106: https://github.com/openresty/headers-more-nginx-module/archive/refs/tags/v%{headers_more_version}.tar.gz
Source107: https://github.com/owasp-modsecurity/ModSecurity-nginx/archive/refs/tags/v%{modsecurity_nginx_version}.tar.gz

License: BSD
Group: System Environment/Daemons
URL: http://nginx.org
BuildRequires: pcre2-devel zlib-devel make gcc systemd libmodsecurity-devel
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
nginx is a high performance web server. It is known for its stability,
efficiency, and flexibility. This build includes lua and modsecurity plugins.

%prep
cp %{SOURCE1} %{SOURCE2} %{SOURCE3} .
%setup -n nginx-%{version}
# Unpack all lua dependencies
tar -xzvf %{SOURCE100} -C %{_builddir}
%global SOURCE100 %{_builddir}/lua-nginx-module-%{lua_nginx_module_version}
tar -xzvf %{SOURCE101} -C %{_builddir}
%global SOURCE101 %{_builddir}/luajit2-%{luajit2_version}
tar -xzvf %{SOURCE102} -C %{_builddir}
%global SOURCE102 %{_builddir}/ngx_devel_kit-%{ngx_devel_kit_version}
tar -xzvf %{SOURCE103} -C %{_builddir}
%global SOURCE103 %{_builddir}/lua-resty-core-%{lua_resty_core_version}
tar -xzvf %{SOURCE104} -C %{_builddir}
%global SOURCE104 %{_builddir}/lua-resty-lrucache-%{lua_resty_lrucache_version}
tar -xzvf %{SOURCE105} -C %{_builddir}
%global SOURCE105 %{_builddir}/ngx_http_redis-%{ngx_http_redis_version}
tar -xzvf %{SOURCE106} -C %{_builddir}
%global SOURCE106 %{_builddir}/headers-more-nginx-module-%{headers_more_version}
tar -xzvf %{SOURCE107} -C %{_builddir}
%global SOURCE107 %{_builddir}/ModSecurity-nginx-%{modsecurity_nginx_version}

# Build luajit
cd %{SOURCE101} && make && make install PREFIX=/usr DESTDIR=%{buildroot}/../luajit
cp -r %{buildroot}/../luajit/* /

%build
export LUAJIT_LIB=/usr/lib
export LUAJIT_INC=/usr/include/luajit-2.1
export DESTDIR=%{buildroot}
nginx_ldopts="$RPM_LD_FLAGS -Wl,-E"
./configure \
    --prefix=%{_datadir}/nginx \
    --sbin-path=%{_sbindir}/nginx \
    --modules-path=%{nginx_moduledir} \
    --conf-path=%{_sysconfdir}/nginx/nginx.conf \
    --error-log-path=%{_localstatedir}/log/nginx/error.log \
    --http-log-path=%{_localstatedir}/log/nginx/access.log \
    --http-client-body-temp-path=%{_localstatedir}/lib/nginx/tmp/client_body \
    --http-proxy-temp-path=%{_localstatedir}/lib/nginx/tmp/proxy \
    --http-fastcgi-temp-path=%{_localstatedir}/lib/nginx/tmp/fastcgi \
    --http-uwsgi-temp-path=%{_localstatedir}/lib/nginx/tmp/uwsgi \
    --http-scgi-temp-path=%{_localstatedir}/lib/nginx/tmp/scgi \
    --pid-path=/run/nginx.pid \
    --lock-path=/run/lock/subsys/nginx \
    --user=%{nginx_user} \
    --group=%{nginx_user} \
    --with-compat \
    --with-file-aio \
    --with-http_gunzip_module \
    --with-http_gzip_static_module \
    --with-http_random_index_module \
    --with-http_realip_module \
    --with-http_secure_link_module \
    --with-http_slice_module \
    --with-http_stub_status_module \
    --with-http_sub_module \
    --with-pcre \
    --with-pcre-jit \
    --with-stream=dynamic \
    --with-stream_realip_module \
    --with-threads \
    --with-cc-opt="%{optflags} $(pcre2-config --cflags)" \
    --with-ld-opt="$nginx_ldopts" \
    --add-module=%{SOURCE100} \
    --add-module=%{SOURCE102} \
    --add-module=%{SOURCE105} \
    --add-module=%{SOURCE106} \
    --add-module=%{SOURCE107}

%make_build

%install
%make_install INSTALLDIRS=vendor
cp -r %{buildroot}/../luajit/* %{buildroot}
cd %{SOURCE103} && make install DESTDIR=%{buildroot}
cd %{SOURCE104} && make install DESTDIR=%{buildroot}

find %{buildroot} -type f -name .packlist -exec rm -f '{}' \;
find %{buildroot} -type f -name perllocal.pod -exec rm -f '{}' \;
find %{buildroot} -type f -empty -exec rm -f '{}' \;
find %{buildroot} -type f -iname '*.so' -exec chmod 0755 '{}' \;
rm -rf %{buildroot}/usr/share/man/man1/luajit.1.gz
rm -rf %{buildroot}/usr/lib/pkgconfig/luajit.pc
rm -rf %{buildroot}/usr/lib/libluajit-5.1.a

install -p -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/nginx.service
install -p -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/nginx
install -p -D -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/nginx/nginx.conf

install -p -d -m 0755 %{buildroot}%{_sysconfdir}/systemd/system/nginx.service.d
install -p -d -m 0755 %{buildroot}%{_unitdir}/nginx.service.d
install -p -d -m 0755 %{buildroot}%{_sysconfdir}/nginx/conf.d
install -p -d -m 0755 %{buildroot}%{_sysconfdir}/nginx/default.d
install -p -d -m 0700 %{buildroot}%{_localstatedir}/lib/nginx
install -p -d -m 0700 %{buildroot}%{_localstatedir}/lib/nginx/tmp
install -p -d -m 0700 %{buildroot}%{_localstatedir}/log/nginx
install -p -d -m 0755 %{buildroot}%{_datadir}/nginx/html
install -p -d -m 0755 %{buildroot}%{nginx_moduleconfdir}
install -p -d -m 0755 %{buildroot}%{nginx_moduledir}
echo 'load_module "%{nginx_moduledir}/ngx_stream_module.so";' > %{buildroot}%{nginx_moduleconfdir}/mod-stream.conf

%clean
rm -rf %{buildroot}
rm -rf %{buildroot}/../luajit

%post
%systemd_post nginx.service

%preun
%systemd_preun nginx.service


%files
%{_datadir}/nginx/html/*
%{_unitdir}/nginx.service
%{_sbindir}/nginx
%config(noreplace) %{_sysconfdir}/nginx/fastcgi.conf
%config(noreplace) %{_sysconfdir}/nginx/fastcgi.conf.default
%config(noreplace) %{_sysconfdir}/nginx/fastcgi_params
%config(noreplace) %{_sysconfdir}/nginx/fastcgi_params.default
%config(noreplace) %{_sysconfdir}/nginx/koi-utf
%config(noreplace) %{_sysconfdir}/nginx/koi-win
%config(noreplace) %{_sysconfdir}/nginx/mime.types
%config(noreplace) %{_sysconfdir}/nginx/mime.types.default
%config(noreplace) %{_sysconfdir}/nginx/nginx.conf
%config(noreplace) %{_sysconfdir}/nginx/nginx.conf.default
%config(noreplace) %{_sysconfdir}/nginx/scgi_params
%config(noreplace) %{_sysconfdir}/nginx/scgi_params.default
%config(noreplace) %{_sysconfdir}/nginx/uwsgi_params
%config(noreplace) %{_sysconfdir}/nginx/uwsgi_params.default
%config(noreplace) %{_sysconfdir}/nginx/win-utf
%config(noreplace) %{_sysconfdir}/logrotate.d/nginx
%attr(770,%{nginx_user},root) %dir %{_localstatedir}/lib/nginx
%attr(770,%{nginx_user},root) %dir %{_localstatedir}/lib/nginx/tmp
%attr(711,root,root) %dir %{_localstatedir}/log/nginx
%ghost %attr(640,%{nginx_user},root) %{_localstatedir}/log/nginx/access.log
%ghost %attr(640,%{nginx_user},root) %{_localstatedir}/log/nginx/error.log
%dir %{nginx_moduledir}
%dir %{nginx_moduleconfdir}
%{nginx_moduleconfdir}/mod-stream.conf
%{nginx_moduledir}/ngx_stream_module.so
%dir %{_datadir}/nginx
%dir %{_datadir}/nginx/html
%dir %{_sysconfdir}/nginx
%dir %{_sysconfdir}/nginx/conf.d
%dir %{_sysconfdir}/nginx/default.d
%dir %{_sysconfdir}/systemd/system/nginx.service.d
%dir %{_unitdir}/nginx.service.d
# lua files
%{_bindir}/luajit*
%{lua_lib}/libluajit-*.so
%{lua_lib}/libluajit-*.so.*
%{_includedir}/luajit-2.1/*
%{_datadir}/luajit-2.1/*
%{_mandir}/man1/luajit.1.gz
%{lua_local_lib}/*

%pre
getent group %{nginx_user} > /dev/null || groupadd -r %{nginx_user}
getent passwd %{nginx_user} > /dev/null || useradd -r -d %{_localstatedir}/lib/nginx -g %{nginx_user} -s /sbin/nologin -c "Nginx web server" %{nginx_user}
exit 0

%changelog
%autochangelog
