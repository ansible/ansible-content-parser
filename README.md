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

## Execution

`ansible-content-parser` accepts two positional parameters: `source` and `output`.

### Source

The first positional parameter is `source`, which specifies
the source repository to be used. Following three types of sources are supported:

1. File directory.
2. Archive file in the following table:

| File Format      | File Extension                                |
| ---------------- | --------------------------------------------- |
| ZIP              | .zip                                          |
| Uncompressed TAR | .tar                                          |
| Compressed TAR   | .tar.gz, .tgz, .tar.bz2, .tbz2, .tar.xz, .txz |

3. Git URL that starts with `https://` or `git@`.

### Output

The second positional parameter is `output`, which specifies a writable
directory. If the directory already exists, it has to be
an empty directory. If it does not exist, it will be newly created with
the given name.

`ansible-content-parser` creates the`repository` subdirectory in the
`output` directory and copies the contents of the `source` repository
to it. The copied contents may be changed by during the execution
of `ansible-content-parser`.

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
