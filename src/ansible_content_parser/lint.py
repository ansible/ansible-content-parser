import pathlib
import sys
from pathlib import Path
from ansiblelint.runner import LintResult

from ansiblelint.__main__ import (
    __version__,
    _do_list,
    _do_transform,
    _logger,
    _perform_mockings_cleanup,
    cache_dir_lock,
    escape,
    get_app,
    get_deps_versions,
    get_version_warning,
    initialize_logger,
    initialize_options,
    load_ignore_txt,
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

def ansiblelint_main(argv: list[str] = None) -> LintResult:

    # FROM HERE ---- COPIED FROM ansiblelint/__main__.py
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

    if options.write_list:
        ruamel_safe_version = "0.17.26"
        from packaging.version import Version
        from ruamel.yaml import __version__ as ruamel_yaml_version_str

        if Version(ruamel_safe_version) > Version(ruamel_yaml_version_str):
            _logger.warning(
                "We detected use of `--write` feature with a buggy ruamel-yaml %s library instead of >=%s, upgrade it before reporting any bugs like dropped comments.",
                ruamel_yaml_version_str,
                ruamel_safe_version,
            )
        _do_transform(result, options)

    mark_as_success = True

    if options.strict and result.matches:
        mark_as_success = False

    # Remove skip_list items from the result
    result.matches = [m for m in result.matches if m.tag not in app.options.skip_list]
    # Mark matches as ignored inside ignore file
    ignore_map = load_ignore_txt(options.ignore_file)
    for match in result.matches:
        if match.tag in ignore_map[match.filename]:
            match.ignored = True

    app.render_matches(result.matches)

    _perform_mockings_cleanup(app.options)
    if cache_dir_lock:
        cache_dir_lock.release()
        pathlib.Path(cache_dir_lock.lock_file).unlink(missing_ok=True)
    if options.mock_filters:
        _logger.warning(
            "The following filters were mocked during the run: %s",
            ",".join(options.mock_filters),
        )

    # TO HERE ---- COPIED FROM ansiblelint/__main__.py
    app.report_outcome(result, mark_as_success=mark_as_success)


    return result, mark_as_success
