FROM registry.access.redhat.com/ubi9/ubi:latest

RUN dnf install -y \
    python3.11 \
    python3.11-pip \
    git
RUN dnf clean dbcache

WORKDIR /var/tmp
COPY dist/ansible_content_parser-*.whl .
RUN pip3.11 install --upgrade pip
RUN pip3.11 install ansible_content_parser-*.whl
RUN rm ansible_content_parser-*.whl

CMD ansible-content-parser
