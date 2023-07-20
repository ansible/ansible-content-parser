import sys
from pathlib import Path
from ansible.parsing.yaml.objects import AnsibleMapping
from collections import Counter

from ansiblelint.__main__ import (
    __version__,
    _do_list,
    _logger,
    escape,
    get_app,
    get_deps_versions,
    get_version_warning,
    initialize_logger,
    initialize_options,
    log_entries,
    options,
    path_inject,
    support_banner,
)

from ansiblelint.color import (
    console,
    console_options,
    reconfigure,
)

known_fields = ['always_run', 'args', 'async', 'become', 'become_flags', 'become_method', 'become_user', 'changed_when',
                'check_mode', 'connection', 'delay', 'delegate_facts', 'delegate_to', 'diff', 'environment',
                'failed_when', 'ignore_errors', 'ignore_unreachable', 'loop', 'loop_control', 'no_log', 'notify',
                'poll', 'register', 'remote_user', 'retries', 'run_once', 'sudo', 'sudo_user', 'tags', 'until', 'vars',
                'when', 'with_dict', 'with_fileglob', 'with_first_found', 'with_flattened', 'with_together',
                'with_subelements', 'with_inventory_hostnames', 'with_items', 'with_indexed_items', 'with_nested']


# FROM HERE ---- COPIED FROM ansiblelint/__main__.py
def main(argv: list[str] | None = None) -> int:
    """Linter CLI entry point."""
    # alter PATH if needed (venv support)
    path_inject()

    if argv is None:  # pragma: no cover
        argv = sys.argv
    initialize_options(argv[1:])

    console_options["force_terminal"] = options.colored
    reconfigure(console_options)

    if options.version:
        deps = get_deps_versions()
        msg = f"ansible-lint [repr.number]{__version__}[/] using[dim]"
        for k, v in deps.items():
            msg += f" {escape(k)}:[repr.number]{v}[/]"
        msg += "[/]"
        console.print(msg, markup=True, highlight=False)
        msg = get_version_warning()
        if msg:
            console.print(msg)
        support_banner()
        sys.exit(0)
    else:
        support_banner()

    initialize_logger(options.verbosity)
    for level, message in log_entries:
        _logger.log(level, message)
    _logger.debug("Options: %s", options)
    _logger.debug("CWD: %s", Path.cwd())

    if not options.offline:
        # pylint: disable=import-outside-toplevel
        from ansiblelint.schemas.__main__ import refresh_schemas

        refresh_schemas()

    # pylint: disable=import-outside-toplevel
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import _get_matches

    if options.list_profiles:
        from ansiblelint.generate_docs import profiles_as_rich

        console.print(profiles_as_rich())
        return 0

    app = get_app(offline=None)  # to be sure we use the offline value from settings
    rules = RulesCollection(
        options.rulesdirs,
        profile_name=options.profile,
        app=app,
        options=options,
    )

    if options.list_rules or options.list_tags:
        return _do_list(rules)

    if isinstance(options.tags, str):
        options.tags = options.tags.split(",")  # pragma: no cover
    result = _get_matches(rules, options)
    # TO HERE ---- COPIED FROM ansiblelint/__main__.py

    print('----')
    print('[ List of files recognized by ansible-lint ]')
    kinds = {l.filename: l.kind for l in result.files}
    for filename in sorted(kinds):
        if kinds[filename] != '':   # Skip files that was not recognized by ansible-lint
            print(f'{filename} - {kinds[filename]}')
    print('----')
    print('[ File counts per kind ]')
    counts = Counter(kinds.values())
    for kind in sorted(counts, key=lambda x: counts[x], reverse=True):
        kind_str = '(not recognized)' if kind == '' else kind
        print(f'{kind_str} - {counts[kind]}')
    print('----')
    print('[ Tasks found in playbooks ]')
    for f in result.files:
        if f.kind == 'playbook':
            print(f"[{f.filename}]")
            tasks = []
            for seq in f.state:
                if isinstance(seq, AnsibleMapping) and ('tasks' in seq):
                    for task in seq['tasks']:
                        if 'name' in task:
                            keys = [key for key in task
                                    if key != 'name' and not key.startswith('__') and key not in known_fields]
                            tasks.append(f"  TASK: name={task['name']} {keys}")
                        elif 'import_tasks' in task:
                            tasks.append(f"  TASK: import_tasks={task['import_tasks']}")
                        else:
                            print(f"???  {task}")
            if len(tasks):
                for task in tasks:
                    print(task)

    return 0

if __name__ == '__main__':
    main(sys.argv)