import json
import sys

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansible.parsing.yaml.objects import AnsibleMapping, AnsibleSequence

from ansiblelint_main import ansiblelint_main


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
            if not (k.startswith('__') or k.endswith('__'))
        }

class MatchErrorDict(dict):
    def __init__(self, matchError: MatchError):
        self['column'] = matchError.column
        self['details'] = matchError.details
        self['filename'] = matchError.filename
        self['fixed'] = matchError.fixed
        self['ignored'] = matchError.ignored
        self['level'] = matchError.level
        self['lineno'] = matchError.lineno
        self['match_type'] = None if matchError.match_type is None else str(matchError.match_type)
        self['message'] = matchError.message
        self['rule'] = matchError.rule.id
        self['tag'] = matchError.tag
        self['task'] = None if matchError.task is None else matchError.task.name


def main(argv: list[str] | None = None) -> int:
    try:
        result = ansiblelint_main(argv)
        serializable_result = {
            "files": [LintableDict(lintable) for lintable in result.files],
            "matches": [MatchErrorDict(matchError) for matchError in result.matches]
        }
        print(json.dumps(serializable_result, indent=2))
        return 0
    except Exception as exc:
        print(str(exc), sys.stderr)
        return -1

if __name__ == '__main__':
    main(sys.argv)