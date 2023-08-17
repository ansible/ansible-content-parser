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
        print(f'{kind} - {counts[kind]}')
    return summary

def report(json_file: str):

    with open(json_file) as f:
        result = json.load(f)
        files = result['files']

    print('----')
    print('[ List of files with identified file types ]')
    kinds = {f['filename']: f['kind'] for f in files}
    for filename in sorted(kinds):
        if kinds[filename] != '':   # Skip files that was not identified by ansible-lint
            print(f'{filename} - {kinds[filename]}')

    print('----')
    print('[ File counts per type ]')
    filetype_summary(result)

    return 0

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('json_file', help='JSON file used as the input for report generation.')
    args = parser.parse_args()

    if not args.json_file:
        parser.print_help()
        return 1

    return report(args.json_file)


if __name__ == '__main__':
    main()
