# ansible-content-parser

## Setup

```
pip3 install -r requirements.txt
```

## Manual Test
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
3. Execute the parser
```commandline
python3 ../ansible-content-parser/parser.py -v ansible-for-devops
```

If the code runs successfully, you'll see outputs like:
```commandline
 $ python3 ../ansible-content-parser/parser.py -v ansible-for-devops
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
INFO     Executing syntax check on playbook ansible-for-devops/deployments-rolling/playbooks/vars.yml (0.57s)
INFO     Executing syntax check on playbook ansible-for-devops/tests/galaxy-role-servers.yml (0.57s)
  :
  :
INFO     Executing syntax check on playbook ansible-for-devops/deployments-rolling/playbooks/provision.yml (0.45s)
INFO     Executing syntax check on playbook ansible-for-devops/tests/elk.yml (0.49s)
----
[ List of files recognized by ansible-lint ]
ansible-for-devops/.github/FUNDING.yml - yaml
ansible-for-devops/.github/workflows/ci.yml - yaml
ansible-for-devops/.github/workflows/molecule-ci.yml - yaml
ansible-for-devops/collection/collections/ansible_collections/local/colors/galaxy.yml - galaxy
ansible-for-devops/collection/collections/ansible_collections/local/colors/plugins/test/blue.py - plugin
ansible-for-devops/collection/main.yml - playbook
  :
  :
ansible-for-devops/tests/solr.yml - playbook
ansible-for-devops/tests/test-plugin.yml - playbook
----
[ File counts per kind ]
(not recognized) - 99
playbook - 69
yaml - 17
requirements - 14
jinja2 - 11
tasks - 11
vars - 7
python - 4
meta - 2
plugin - 1
text - 1
handlers - 1
galaxy - 1
----
[ Tasks found in playbooks ]
[ansible-for-devops/deployments/playbooks/deploy.yml]
  TASK: name=Ensure demo application is at correct release. ['git']
  TASK: name=Ensure secrets file is present. ['template']
  TASK: name=Install required dependencies with bundler. ['command']
  TASK: name=Check if database exists. ['stat']
  TASK: name=Create database. ['command']
  TASK: name=Perform deployment-related rake tasks. ['command']
  TASK: name=Ensure demo application has correct user for files. ['file']
[ansible-for-devops/deployments-rolling/playbooks/vars.yml]
[ansible-for-devops/tests/nodejs.yml]
  TASK: name=Install firewalld so we can disable it in the playbook. ['dnf']
[ansible-for-devops/tests/docker-flask.yml]
[ansible-for-devops/elk/provisioning/web/main.yml]
  TASK: name=Set up virtual host for testing. ['copy']
  TASK: name=Ensure logs server is in hosts file. ['lineinfile']
  :
  :
```