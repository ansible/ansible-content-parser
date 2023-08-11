FROM registry.access.redhat.com/ubi9/ubi:latest

RUN dnf install -y \
    python3.11 \
    python3.11-pip
RUN dnf clean dbcache

COPY ansible_content_parser /var/ansible_content_parser/ansible_content_parser
COPY requirements.txt /var/ansible_content_parser
COPY pipeline.sh /var/ansible_content_parser
COPY ari /var/ari

WORKDIR /var/ansible_content_parser
RUN pip3.11 install -r requirements.txt --no-cache-dir

CMD /var/ansible_content_parser/pipeline.sh
