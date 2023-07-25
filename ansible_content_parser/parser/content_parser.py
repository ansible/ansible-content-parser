import contextlib
import json
import os
import sys

from ansiblelint.file_utils import Lintable
from ansiblelint.formatters import CodeclimateJSONFormatter
from ansible.parsing.yaml.objects import AnsibleMapping, AnsibleSequence

from parser.lint import ansiblelint_main
from pathlib import Path


class LintableDict(dict):
    def __init__(self, lintable: Lintable):

        self['name'] = str(lintable.path.name) # str(lintable.name) set a name without the directory
        self['kind'] = str(lintable.kind)
        self['filename'] = str(lintable.filename)
        self['dir'] = str(lintable.dir)
        self['exc'] = None if lintable.exc is None else str(lintable.exc)
        self['role'] = str(lintable.role)
        self['state'] = self.parse_ansible_object(lintable.state)

    def parse_ansible_object(self, o: any):
        if isinstance(o, AnsibleSequence):
            return self.parse_ansible_sequence(o)
        elif isinstance(o, AnsibleMapping):
            return self.parse_ansible_mapping(o)
        else:
            return str(o)

    def parse_ansible_sequence(self, o: AnsibleSequence):
        return [self.parse_ansible_object(e) for e in o]

    def parse_ansible_mapping(self, o: AnsibleMapping):
        return {
            k:self.parse_ansible_object(v)
            for k,v in o.items()
            if not isinstance(k, str) or not (k.startswith('__') or k.endswith('__'))
        }

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

def execute_ansiblelint(argv, work_dir='../work'):
    with pushd(work_dir):
        result, mark_as_success = ansiblelint_main(argv)
        serializable_result = {
            "files": [LintableDict(lintable) for lintable in result.files],
            "matches": get_matches(result.matches)
        }
        with open(os.path.join(work_dir,'result.json'), 'w') as f:
            f.write(json.dumps(serializable_result, indent=2))
    return serializable_result

def main(argv: list[str] | None = None) -> int:
    try:
        serializable_result = execute_ansiblelint(argv)
        print(json.dumps(serializable_result, indent=2))
        return 0
    except Exception as exc:
        print(str(exc), sys.stderr)
        return -1

if __name__ == '__main__':
    main(sys.argv)