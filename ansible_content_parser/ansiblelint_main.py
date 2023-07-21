import sys
from pathlib import Path
from ansiblelint.runner import LintResult

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

def ansiblelint_main(argv: list[str] | None = None) -> LintResult:

    # FROM HERE ---- COPIED FROM ansiblelint/ansiblelint_main.py
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
    # TO HERE ---- COPIED FROM ansiblelint/ansiblelint_main.py

    return result

