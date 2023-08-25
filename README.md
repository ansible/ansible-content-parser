# ansible-content-parser

## Overview

`ansible-content-parser` used for analyze Ansible files, such
as playbooks, task files, etc. in a given directory.

It runs `ansible-lint` internally against a given
source directory and
updates Ansible files (the `--write` option of `ansible-lint`)
and generates the `lint-result.json` file, which summarizes
files found in the directory and lint errors.

## Build

Execute the `tox` command. Installable images are created under
the `dist` directory.

## lint-result.json

`lint-result.json` is created as the result of the execution
of `ansible-content-parser`. The file contains a dictionary, which
has one key/value pairs:

1. `files` This is for the list of files that were found
   in the execution. The format of each file entry is explained below.

### Format of the file entry

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

#### Example

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
