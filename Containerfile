FROM fedora:41

RUN dnf install rpm-build dnf-utils tree -y

COPY nginx.service nginx.logrotate nginx.conf /root/rpmbuild/SOURCES/
COPY nginx.spec /root/rpmbuild/SPECS/
RUN yum-builddep -y /root/rpmbuild/SPECS/nginx.spec
