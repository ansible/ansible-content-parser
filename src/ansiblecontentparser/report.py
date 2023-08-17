import argparse
import json

from collections import Counter

def filetype_summary(result):
    kinds = {f['filename']: f['kind'] for f in result['files']}
    counts = Counter(kinds.values())
    summary = []
    for kind in sorted(counts, key=lambda x: counts[x], reverse=True):
        kind_str = '(file type not identified)' if kind == '' else kind
        summary.append((kind_str, counts[kind]))
        print(f'{kind_str} - {counts[kind]}')
    return summary

def module_summary(findings_json):
    modules = []
    for line in open(findings_json):
        finding = json.loads(line)
        root_definitions = finding.get('root_definitions')
        if root_definitions:
            definitions = root_definitions.get('definitions')
            if definitions:
                tasks = definitions.get('tasks')
                if tasks:
                    for task in tasks:
                        module = task.get('module')

                        module_info = task.get('module_info')
                        if module_info:
                            module = module_info.get('fqcn')
                        if module:
                            modules.append(module)
    module_counts = Counter(modules)
    for module in sorted(module_counts, key=lambda x: module_counts[x], reverse=True):
        print(f'{module} - {module_counts[module]}')

def report(json_file: str, findings_json: str):

    import datetime
    timenow = datetime.datetime.now().isoformat()
    version = 'V0.0.1'
    input = 'git@github.com:IBM/Ansible-OpenShift-Provisioning.git'

    print(f'''**** Ansible Content Parser {version} ****
[ Execution summary ]
Date/Time: {timenow}
Input: {input}
    ''')

    with open(json_file) as f:
        result = json.load(f)
        files = result['files']

    print('----')
    print('[ File counts per file type ]')
    filetype_summary(result)

    print('----')
    print('[ Ansible module counts ]')
    module_summary(findings_json)

    print('----')
    print('[ List of Ansible files with file types ]')
    kinds = {f['filename']: f['kind'] for f in files}
    for filename in sorted(kinds):
        if kinds[filename] != '':   # Skip files that was not identified by ansible-lint
            print(f'{filename} - {kinds[filename]}')

    print('----')
    print('[ Issues found by ansible-lint ]')
    for match in result['matches']:
        print(f'Type: {match["type"]}')
        print(f'Severity: {match["severity"]}')
        print(f'Path: {match["location"]["path"]}')
        if 'positions' in match["location"] and 'begin' in match["location"]["positions"]:
            print(f'Line: {match["location"]["positions"]["begin"]["line"]}')
        print(f'Description: {match["description"]}')
        print()
    print('----')

    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('json_file', help='JSON file used as the input for report generation.')
    parser.add_argument('findings_json', help='Findings')
    args = parser.parse_args()

    if not args.json_file:
        parser.print_help()
        return 1

    return report(args.json_file, args.findings_json)


if __name__ == '__main__':
    main()
