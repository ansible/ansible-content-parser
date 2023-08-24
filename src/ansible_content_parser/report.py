import argparse
import json
import sys

from collections import Counter

def filetype_summary(result, f):
    kinds = {f['filename']: f['kind'] for f in result['files']}
    counts = Counter(kinds.values())
    summary = []
    for kind in sorted(counts, key=lambda x: counts[x], reverse=True):
        kind_str = '(file type not identified)' if kind == '' else kind
        summary.append((kind_str, counts[kind]))
        print(f'{kind_str} - {counts[kind]}', file=f)
    return summary

def module_summary(sage_objects_json, f):
    modules = []
    for line in open(sage_objects_json):
        sage_obj = json.loads(line)
        type = sage_obj.get('type')
        if type == 'task':
            executable_type = sage_obj.get('executable_type')
            if executable_type == 'Module':
                module = sage_obj.get('module')
                resolved_name = sage_obj.get('resolved_name')
                if resolved_name:
                    module = resolved_name
                modules.append(module)
    module_counts = Counter(modules)
    for module in sorted(module_counts, key=lambda x: module_counts[x], reverse=True):
        print(f'{module} - {module_counts[module]}', file=f)

def report(file_list: str, sarif_file:str, sage_objects_json: str, report_file: str):

    with (open(report_file, 'w') if report_file else sys.stdout) as f:
        import datetime
        timenow = datetime.datetime.now().isoformat()
        version = 'V0.0.1'
        input = 'git@github.com:IBM/Ansible-OpenShift-Provisioning.git'

        print(f'''**** Ansible Content Parser {version} ****
[ Execution summary ]
Date/Time: {timenow}
Input: {input}
        ''', file=f)

        with open(file_list) as jsonf:
            result = json.load(jsonf)
            files = result['files']

        with open(sarif_file) as sarif:
            r = json.load(sarif)
            matches = r['runs'][0]['results']

        print('----', file=f)
        print('[ File counts per file type ]', file=f)
        filetype_summary(result, f)

        print('----', file=f)
        print('[ Ansible module counts ]', file=f)
        module_summary(sage_objects_json, f)

        print('----', file=f)
        kinds = {f['filename']: f['kind'] for f in files}
        for filename in sorted(kinds):
            if kinds[filename] != '':   # Skip files that was not identified by ansible-lint
                print(f'{filename} - {kinds[filename]}', file=f)

        print('----', file=f)
        print('[ Issues found by ansible-lint ]', file=f)
        for match in matches:
            print(f'Type: {match["ruleId"]}', file=f)
            print(f'Path: {match["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]}', file=f)
            print(f'Line: {match["locations"][0]["physicalLocation"]["region"]["startLine"]}', file=f)
            print(f'Description: {match["message"]["text"]}', file=f)
            print(file=f)
        print('----', file=f)

    return 0

def main(argv) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('file_list', help='File list processed by ansible-lint')
    parser.add_argument('sarif_file', help='SARIF JSON output from ansible-lint')
    parser.add_argument('sage_objects_json', help='sage objects')
    parser.add_argument('report_file', nargs='?', default=None, help='report_output')
    args = parser.parse_args(argv)

    if not args.file_list:
        parser.print_help()
        return 1

    return report(args.file_list, args.sarif_file, args.sage_objects_json, args.report_file)


if __name__ == '__main__':
    main(sys.argv[1:])
