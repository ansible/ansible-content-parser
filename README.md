# ansible-content-parser

## Overview

As of today (2023-07-21) this repository contains a very early 
PoC for [AAP-12832](https://issues.redhat.com/browse/AAP-12832).

Three Python scripts are implemented in the `ansible_content_parser` subdirectory:

- **ansiblelint_main.py** This was built based on the `main()` routine of the 
`ansible-lint` tool. It invokes `ansible-lint` in the same way as the original code does, but
returns the internal `LintResult` object, which contains the detailed information about the execution.
- **parser.py** This file provides the`main()` routine of the parser. It invokes `ansible-lint`
using the `ansiblelint_main()` method exported in `ansiblelint_main.py` and convert the returned
`LintResult` object into a JSON string.
- **report.py** This is a utility program to process the JSON data generated by `parser.py`.

## Setup

```
pip3 install -r requirements.txt
```

## Execution
1. Create the work directory `work` under the project root and
change the current directory
```commandline
mkdir work
cd work
```
2. Clone a test repository
```commandline
git clone https://github.com/geerlingguy/ansible-for-devops.git
```
3. Execute the parser and redirect the output to a JSON file
```commandline
python3 ../ansible-content-parser/parser.py -v ansible-for-devops > result.json
```

If the code runs successfully, you'll see outputs (note: they appear in stderr) like:
```commandline
$ python3 ../ansible_content_parser/parser.py -v ansible-for-devops > result.json
INFO     Identified /home/ttakamiy/git/ansible/ansible-content-parser/work/ansible-for-devops as project root due .git directory.
INFO     Set ANSIBLE_LIBRARY=/home/ttakamiy/.cache/ansible-compat/00e13e/modules:/home/ttakamiy/.ansible/plugins/modules:/usr/share/ansible/plugins/modules
INFO     Set ANSIBLE_COLLECTIONS_PATH=/home/ttakamiy/.cache/ansible-compat/00e13e/collections:/home/ttakamiy/.ansible/collections:/usr/share/ansible/collections
INFO     Set ANSIBLE_ROLES_PATH=/home/ttakamiy/.cache/ansible-compat/00e13e/roles:/home/ttakamiy/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles
INFO     Loading ignores from ansible-for-devops/.gitignore
INFO     Excluded: ansible-for-devops/.git
INFO     Loading ignores from ansible-for-devops/https-letsencrypt/.gitignore
INFO     Loading ignores from ansible-for-devops/kubernetes/examples/files/.gitignore
INFO     Set ANSIBLE_LIBRARY=/home/ttakamiy/.cache/ansible-compat/00e13e/modules:/home/ttakamiy/.ansible/plugins/modules:/usr/share/ansible/plugins/modules
INFO     Set ANSIBLE_COLLECTIONS_PATH=/home/ttakamiy/.cache/ansible-compat/00e13e/collections:/home/ttakamiy/.ansible/collections:/usr/share/ansible/collections
INFO     Set ANSIBLE_ROLES_PATH=/home/ttakamiy/.cache/ansible-compat/00e13e/roles:/home/ttakamiy/.ansible/roles:/usr/share/ansible/roles:/etc/ansible/roles
INFO     Executing syntax check on playbook ansible-for-devops/docker-flask/provisioning/main.yml (0.55s)
INFO     Executing syntax check on playbook ansible-for-devops/elk/provisioning/web/main.yml (0.56s)
  :
  :
INFO     Executing syntax check on playbook ansible-for-devops/gluster/playbooks/vars.yml (0.44s)
INFO     Executing syntax check on playbook ansible-for-devops/lamp-infrastructure/provisioners/aws.yml (0.48s)
```

4. Run the report.py using the generated JSON file as the input

```commandline
$ python3 ../ansible_content_parser/report.py result.json                        
----
[ List of files with identified file types ]
ansible-for-devops/.github/FUNDING.yml - yaml
ansible-for-devops/.github/workflows/ci.yml - yaml
ansible-for-devops/.github/workflows/molecule-ci.yml - yaml
ansible-for-devops/collection/collections/ansible_collections/local/colors/galaxy.yml - galaxy
ansible-for-devops/collection/collections/ansible_collections/local/colors/plugins/test/blue.py - plugin
ansible-for-devops/collection/main.yml - playbook
ansible-for-devops/deployments-balancer/playbooks/deploy.yml - playbook
ansible-for-devops/deployments-balancer/playbooks/provision.yml - playbook
  :
  :
ansible-for-devops/tests/solr.yml - playbook
ansible-for-devops/tests/test-plugin.yml - playbook
----
[ File counts per type ]
(file type not identified) - 99
playbook - 69
yaml - 17
requirements - 14
jinja2 - 11
tasks - 11
vars - 7
python - 4
meta - 2
text - 1
handlers - 1
galaxy - 1
plugin - 1
----
[ Tasks found in playbooks ]
[ansible-for-devops/first-ansible-playbook/playbook.yml]
  play-1:
    tasks:
      name=Ensure chrony (for time synchronization) is installed. ['dnf']
      name=Ensure chrony is running. ['service']
  play-2:
    tasks:
???   {'dnf': 'name=chrony state=present'}
???   {'service': 'name=chronyd state=started enabled=yes'}
[ansible-for-devops/tests/nodejs.yml]
  play-1:
    tasks:
      name=Install firewalld so we can disable it in the playbook. ['dnf']
  :
  :
      name=Run Solr installation script. ['command']
      name=Ensure solr is started and enabled on boot. ['service']
[ansible-for-devops/tests/test-plugin.yml]
  play-1:
----
[ File dependencies ]
WARN:  A variable is contained in a file reference: template -> ../templates/{{ item }}.j2
GraphViz dot file dependencies.dot is created.
```

5. Generated Graphviz dot file can be converted into a diagram if you have installed GraphViz
on your machine. For example, for converting the file into a SVG file, run the `dot` command like

```
$ dot -Tsvg dependencies.dot > dependencies.svg
```
You can open the created SVG file in a web browser, such as Chrome/Firefox.