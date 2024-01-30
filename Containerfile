FROM fedora:39

RUN dnf install rpm-build dnf-utils tree -y

COPY nginx.service nginx.logrotate /root/rpmbuild/SOURCES/
COPY nginx.spec /root/rpmbuild/SPECS/
RUN yum-builddep -y /root/rpmbuild/SPECS/nginx.spec
