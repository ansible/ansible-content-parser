import argparse
import json

from collections import Counter

known_fields = ['always_run', 'args', 'async', 'become', 'become_flags', 'become_method', 'become_user', 'changed_when',
                'check_mode', 'connection', 'delay', 'delegate_facts', 'delegate_to', 'diff', 'environment',
                'failed_when', 'ignore_errors', 'ignore_unreachable', 'loop', 'loop_control', 'no_log', 'notify',
                'poll', 'register', 'remote_user', 'retries', 'run_once', 'sudo', 'sudo_user', 'tags', 'until', 'vars',
                'when', 'with_dict', 'with_fileglob', 'with_first_found', 'with_flattened', 'with_together',
                'with_subelements', 'with_inventory_hostnames', 'with_items', 'with_indexed_items', 'with_nested']

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
    counts = Counter(kinds.values())
    for kind in sorted(counts, key=lambda x: counts[x], reverse=True):
        kind_str = '(file type not identified)' if kind == '' else kind
        print(f'{kind_str} - {counts[kind]}')

    print('----')
    print('[ Tasks found in playbooks ]')

    for f in files:
        if f['kind'] == 'playbook':
            print(f"[{f['filename']}]")
            for i, seq in enumerate(f['state']):
                print(f'  play-{i + 1}:')
                for task_type in ['pre_tasks', 'tasks', 'post_tasks']:
                    if task_type in seq:
                        print(f'    {task_type}:')
                        for task in seq[task_type]:
                            if 'name' in task:
                                keys = [key for key in task
                                        if key != 'name' and not key.startswith('__') and key not in known_fields]
                                print(f"      name={task['name']} {keys}")
                            elif 'import_tasks' in task:
                                print(f"      import_tasks={task['import_tasks']}")
                            else:
                                print(f"???   {task}")

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