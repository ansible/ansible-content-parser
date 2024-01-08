# ansible-content-parser

## Overview

`ansible-content-parser` analyzes Ansible files in a given source
(a local directory, an archive file or a git URL)
by running `ansible-lint` internally,
updates Ansible files using the [Autofix feature of `ansible-lint`](https://ansible.readthedocs.io/projects/lint/autofix/)
and generates the `ftdata.jsonl` file, which is the training dataset for
developing custom AI models.

## Build

Execute the `tox` command. Installable images are created under
the `dist` directory.

## Installation

### Prerequisites

- Python version 3.10 or later.
- UNIX OS, such as Linux or Mac OS.

**Note:** Installation on Microsoft Windows OS is not supported.

### Procedure

`ansible-content-parser` uses a newer version of `ansible-lint` and its
dependent components. In order to isolate them from the existing
Ansible installations, it is recommended to install `ansible-content-parser` in
a Python virtual environment with the following steps:

1. Create a working directory and set up venv Python virtual environment:

```commandline
python -m venv ./venv
source ./venv/bin/activate
```

2. Install `ansible-content-parser` from the pip repository:

```commandline
pip install --upgrade pip
pip install --upgrade ansible-content-parser
```

3. After the installation is completed, verify that `ansible-content-parser` and `ansible-lint` are installed correctly:

```commandline
ansible-content-parser --version
ansible-lint --version
```

A list of application versions and their dependencies are displayed.
In the output that is displayed, ensure that you have the same version of `ansible-lint`.

**Important:** If there is a mismatch in the installed `ansible-lint` versions, you cannot get consistent results from the content parser and ansible-lint.
For example, the following result shows a mismatch in `ansible-lint` versions:

```commandline
$ ansible-content-parser --version
ansible-content-parser 0.0.1 using ansible-lint:6.20.0 ansible-core:2.15.4
$ ansible-lint --version
ansible-lint 6.13.1 using ansible 2.15.4
A new release of ansible-lint is available: 6.13.1 → 6.20.0
```

If the `ansible-lint` versions do not match, perform the following tasks:

1. Deactivate and reactivate venv:

```commandline
deactivate
source ./venv/bin/activate
```

2. Verify that the `ansible-lint` versions match:

```commandline
ansible-content-parser --version
ansible-lint --version
```

For example, the following output shows the same ansible-lint versions:

```
$ ansible-content-parser --version
ansible-content-parser 0.0.1 using ansible-lint:6.20.0 ansible-core:2.15.4
$ ansible-lint --version
ansible-lint 6.20.0 using ansible-core:2.15.4 ansible-compat:4.1.10 ruamel-yaml:0.17.32 ruamel-yaml-clib:0.2.7
```

## Execution

`ansible-content-parser` accepts two positional parameters (`source` and `output`)
with a few optional parameters.

```commandline
$ ansible-content-parser --help
usage: ansible-content-parser [-h] [--config-file CONFIG_FILE]
                              [--profile {min,basic,moderate,safety,shared,production}] [--fix WRITE_LIST]
                              [--skip-ansible-lint] [--no-exclude] [-v] [--source-license SOURCE_LICENSE]
                              [--source-description SOURCE_DESCRIPTION] [--repo-name REPO_NAME] [--repo-url REPO_URL]
                              [--version]
                              source output

Parse Ansible files in the given repository by running ansible-lint and generate a training dataset for Ansible
Lightspeed.

positional arguments:
  source                source, which can be an zip/tar archive, a git URL or a local directory
  output                output directory

options:
  -h, --help            show this help message and exit
  --config-file CONFIG_FILE
                        Specify the configuration file to use for ansible-lint. By default it will look for '.ansible-
                        lint', '.config/ansible-lint.yml', or '.config/ansible-lint.yaml' in the source repository.
  --profile {min,basic,moderate,safety,shared,production}
                        Specify which rules profile to be used for ansible-lint
  --fix WRITE_LIST      Specify how ansible-lint performs auto-fixes, including YAML reformatting. You can limit the
                        effective rule transforms (the 'write_list') by passing a keywords 'all' (=default) or 'none'
                        or a comma separated list of rule ids or rule tags.
  -S, --skip-ansible-lint
                        Skip the execution of ansible-lint.
  --no-exclude          Do not let ansible-content-parser to generate training dataset by excluding files that caused
                        lint errors. With this option specified, a single lint error terminates the execution without
                        generating the training dataset.
  -v, --verbose         Explain what is being done
  --source-license SOURCE_LICENSE
                        Specify the license that will be included in the training dataset.
  --source-description SOURCE_DESCRIPTION
                        Specify the description of the source that will be included in the training dataset.
  --repo-name REPO_NAME
                        Specify the repository name that will be included in the training dataset. If it is not
                        specified, it is generated from the source name.
  --repo-url REPO_URL   Specify the repository url that will be included in the training dataset. If it is not
                        specified, it is generated from the source name.
  --version             show program's version number and exit
```

### `source` positional argument

The first positional parameter is `source`, which specifies
the source repository to be used. Following three types of sources are supported:

1. File directory.
2. Archive file in the following table:

| File Format      | File Extension                                |
| ---------------- | --------------------------------------------- |
| ZIP              | .zip                                          |
| Uncompressed TAR | .tar                                          |
| Compressed TAR   | .tar.gz, .tgz, .tar.bz2, .tbz2, .tar.xz, .txz |

3. Git URL, e.g. `git@github.com:ansible/workshop-examples.git` or `https://github.com/ansible/workshop-examples.git`

### `output` positional argument

The second positional parameter is `output`, which specifies a writable
directory. If the directory already exists, it has to be
an empty directory. If it does not exist, it will be newly created with
the given name.

`ansible-content-parser` creates the`repository` subdirectory in the
`output` directory and copies the contents of the `source` repository
to it. The copied contents may be changed by during the execution
of the Content Parser.

## Outputs

Following directory structure is created in the directory specified with the `output`
positional argument.

```
output/
  |-- ftdata.jsonl # Training dataset
  |-- report.txt   # A human-readable report
  |
  |-- repository/
  |     |-- (files copied from the source repository)
  |
  |-- metadata/
        |-- lint-result.json     # Metadata generated by ansible-lint
        |-- sarif.json           # ansible-lint results in SARIF format
        |-- (other metadata files generated)
```

### ftdata.jsonl

This is the training dataset file, which is the main output of `ansible-content-parser`.

It is in the JSONL format, each of whose line represents a JSON object

### report.txt

This is a human-readable report that provides the summary information of the run
of `ansible-content-parser`, which contains sections like:

1. File counts per type
2. List of Ansible files identified
3. Issues found by ansible-lint
4. List of Ansible modules found in tasks

Note: When the `--skip-ansible-lint` option is specified, the first three sections do
not appear in the report.

### metadata directory

This subdirectory contains a few files that contain metadata generated
in the Content Parser run.

#### lint-result.json

`lint-result.json` is created in the `metadata` subdirectory
as the result of the execution
of `ansible-content-parser`. The file contains a dictionary, which
has two key/value pairs:

1. `files` This is for the list of files that were found
   in the execution. The format of each file entry is explained below.

Each file entry is represented as a dictionary that contains following keys

| Key               | Description                                                   |
| ----------------- | ------------------------------------------------------------- |
| `base_kind`       | MIME type of the file, for example, `text/yaml`               |
| `dir`             | Directory where the file resides.                             |
| `exc`             | Exception found while processing this file. It can be null.   |
| `filename`        | File name                                                     |
| `kind`            | File type, for example, `playbook`, `tasks` or `role`         |
| `name`            | File name (Usually same as `filename`)                        |
| `parent`          | Name of the parent, like a role. It can be null               |
| `role`            | Ansible role. It can be null                                  |
| `stop_processing` | Identifies whether processing was stopped on this file or not |
| `updated`         | Identifies whether contents were updated by `ansible-lint`    |

Following shows an example of a file entry:

```json
{
  "base_kind": "text/yaml",
  "dir": "/mnt/input/roles/delete_compute_node/tasks",
  "exc": null,
  "filename": "roles/delete_compute_node/tasks/main.yaml",
  "kind": "tasks",
  "name": "roles/delete_compute_node/tasks/main.yaml",
  "parent": "roles/delete_compute_node",
  "role": "delete_compute_node",
  "stop_processing": false,
  "updated": false
}
```

2.  `excluded` This is for the list of file paths, which were excluded in the second `ansible-lint`
    execution because syntax check errors were found in those files on the first execution.
    The files included in the list will not appear in the entries associated with the `files` key.

- **Note:** If `ansible-content-parser` is executed with the `--no-exclude` option, the second execution
  does not occur even if syntax check errors were found on the first execution and
  the training dataset will not be created.

#### sarif.json

This is the output of `ansible-lint` with the `--sarif-file` option.
The `report.txt` contains a summary generated
from this file in the "Issues found by ansible-lint" section.
