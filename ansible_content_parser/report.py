import argparse
import json
import os
import sys

from collections import Counter

known_fields = ['always_run', 'args', 'async', 'become', 'become_flags', 'become_method', 'become_user', 'changed_when',
                'check_mode', 'connection', 'delay', 'delegate_facts', 'delegate_to', 'diff', 'environment',
                'failed_when', 'ignore_errors', 'ignore_unreachable', 'loop', 'loop_control', 'no_log', 'notify',
                'poll', 'register', 'remote_user', 'retries', 'run_once', 'sudo', 'sudo_user', 'tags', 'until', 'vars',
                'when', 'with_dict', 'with_fileglob', 'with_first_found', 'with_flattened', 'with_together',
                'with_subelements', 'with_inventory_hostnames', 'with_items', 'with_indexed_items', 'with_nested']

fillcolors = {
    "playbook": "pink",
    "tasks": "lightblue",
    "jinja2": "khaki",
    "vars": "lightgreen",
    "yaml": "white",
}

def report(json_file: str, dot_file: str):

    with open(json_file) as f:
        result = json.load(f)
        files = result['files']

    file_dict = {os.path.realpath(f['filename']):f for f in files}

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


    if dot_file:
        generate_graphviz_dot_file(dot_file, files, file_dict)

    return 0


def generate_graphviz_dot_file(dot_file, files, file_dict):
    def drop_repo_name(s: str):
        i = s.index('/')
        return s[i + 1:]

    def option_string(f: dict):
        filename = drop_repo_name(f["filename"])
        i = filename.rfind('/')
        if i >= 0:
            label = filename[:i + 1] + '\\n' + filename[i + 1:]
        else:
            label = filename
        return f'  "{filename}" [label="{label}",fillcolor={fillcolors[f["kind"]]}]\n'

    with open(dot_file, 'w') as dot:
        dot.write('digraph {\n')
        dot.write('  rankdir="LR"\n')
        dot.write('  graph [pad=0.01, nodesep=0.1, ranksep=0.2]')
        dot.write('  node [shape="box", style=filled, fillcolor=lightgray, '
                  'margin=0.05, width=0, height=0, fontname="Sans-Serif", fontsize=10]\n')
        dot.write('  edge [minlen=2, arrowtail=normal, arrowhead=none, dir=both]')

        print('----')
        print('[ File dependencies ]')

        for f in files:
            if f['kind'] in fillcolors.keys():
                dot.write(option_string(f))

        for f in files:
            pwd = f['dir']
            if f['kind'] == 'playbook':
                for i, seq in enumerate(f['state']):
                    def find_element(d, keys, child_element=None):
                        for key in keys:
                            if key in d:
                                if not child_element:
                                    referenced = d[key]
                                else:
                                    referenced = d[key][child_element]

                                if isinstance(referenced, list):
                                    references = referenced
                                else:
                                    references = [referenced]

                                for ref in references:
                                    realpath = os.path.realpath(pwd + '/' + ref)
                                    if realpath.find('{{') >= 0:
                                        print(f"WARN:  A variable is contained in a file reference: {key} -> {ref}")
                                    else:
                                        if realpath in file_dict:
                                            name = drop_repo_name(file_dict[realpath]['filename'])
                                            dot.write(f'  "{drop_repo_name(f["filename"])}" -> "{name}"\n')

                    find_element(seq, ['import_playbook', 'vars_files'])
                    for task_type in ['pre_tasks', 'tasks', 'post_tasks']:
                        if task_type in seq:
                            for task in seq[task_type]:
                                find_element(task, ['import_tasks'])
                                find_element(task, ['template'], 'src')

        dot.write('  subgraph cluster_01 {\n')
        dot.write('    label = "Legend"\n')
        dot.write('    rank = "min"\n')
        for k, v in fillcolors.items():
            dot.write(f'    {k} [fillcolor={v}]\n')
        dot.write('    "(others)" [fillcolor=lightgray]\n')
        dot.write('  }\n')

        dot.write('}')

    print(f'GraphViz dot file {dot_file} is created.')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('json_file', help='JSON file used as the input for report generation.')
    parser.add_argument('-d', '--dot_file', default=None,
                        help='GraphViz DOT file for file dependency output. Default is None')
    args = parser.parse_args()

    if not args.json_file:
        parser.print_help()
        return 1

    return report(args.json_file, args.dot_file)


if __name__ == '__main__':
    main()