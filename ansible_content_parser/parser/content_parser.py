import argparse
import contextlib
import json
import os
import sys

from ansiblelint.file_utils import Lintable
from ansiblelint.formatters import CodeclimateJSONFormatter

from parser.lint import ansiblelint_main
from pathlib import Path


class LintableDict(dict):
    def __init__(self, lintable: Lintable):
        self['base_kind'] = str(lintable.base_kind)
        self['dir'] = str(lintable.dir)
        self['exc'] = None if lintable.exc is None else str(lintable.exc)
        self['filename'] = str(lintable.filename)
        self['kind'] = str(lintable.kind)
        self['name'] = str(lintable.name)
        self['parent'] = None if lintable.parent is None else str(lintable.parent.name)
        self['role'] = str(lintable.role)
        self['stop_processing'] = bool(lintable.stop_processing)
        self['updated'] = bool(lintable.updated)


def get_matches(matches):
    # From ansiblelint/app.py
    """Display given matches (if they are not fixed)."""
    matches = [match for match in matches if not match.fixed]

    formatter = CodeclimateJSONFormatter(Path.cwd(), display_relative_path=True)
    json_string = formatter.format_result(matches)
    return json.loads(json_string)


# https://stackoverflow.com/questions/6194499/pushd-through-os-system
@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


def execute_ansiblelint(argv, work_dir):
    with pushd(work_dir):
        result, mark_as_success = ansiblelint_main(argv)
        serializable_result = {
            "files": [LintableDict(lintable) for lintable in result.files],
            "matches": get_matches(result.matches)
        }
    return serializable_result


def main() -> int:
    parser = argparse.ArgumentParser(description="TODO")
    parser.add_argument("-d", "--dir", help='root direcotry for scan')
    parser.add_argument("-t", "--source-type", help='source type (e.g."GitHub-RHIBM")')
    parser.add_argument("-r", "--repo-name", help='repo name (e.g."IBM/Ansible-OpsnShift-Provisioning")')
    parser.add_argument("-o", "--out-dir", default="", help="output directory for the rule evaluation result")
    args = parser.parse_args()
    print(args)

    if not args.dir or not args.out_dir:
        parser.print_help()
        exit(1)

    argv = ['-v', '--write']

    try:
        serializable_result = execute_ansiblelint(argv, args.dir)
        if not os.path.exists(args.out_dir):
            os.makedirs(args.out_dir)
        with open(os.path.join(args.out_dir, 'lint-result.json'), 'w') as f:
            f.write(json.dumps(serializable_result, indent=2))
        return 0
    except Exception as exc:
        print(str(exc), sys.stderr)
        return -1


if __name__ == '__main__':
    main()
