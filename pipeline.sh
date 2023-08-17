#!/usr/bin/env bash
PYTHONPATH=$PYTHONPATH:/var/ansible_content_parser/ansible_content_parser \
  /usr/bin/python3.11 \
  /var/ansible_content_parser/ansible_content_parser/parser/content_parser.py \
  -d /mnt/input \
  -o /mnt/output

retVal=$?
if [ $retVal -ne 0 ]; then
    echo "Error in running ansible-lint"
    exit $retVal
fi

exit $retVal
