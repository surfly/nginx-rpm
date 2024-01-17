FROM fedora:39

RUN dnf install rpm-build dnf-utils rpmdevtools tree -y

COPY nginx.service nginx.logrotate /root/rpmbuild/SOURCES/
COPY nginx.spec /root/rpmbuild/SPECS/
RUN yum-builddep -y /root/rpmbuild/SPECS/nginx.spec
RUN spectool -g -R /root/rpmbuild/SPECS/nginx.spec
