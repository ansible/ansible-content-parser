"""Invoke ansible-lint."""
from __future__ import annotations

import sys

from pathlib import Path
from typing import TYPE_CHECKING

from ansiblelint.__main__ import (
    _do_transform,
    _logger,
    _perform_mockings_cleanup,
    get_app,
    initialize_logger,
    initialize_options,
    load_ignore_txt,
    log_entries,
    options,
    path_inject,
)
from ansiblelint.color import (
    console_options,
    reconfigure,
)


if TYPE_CHECKING:
    from ansiblelint.runner import LintResult


# pylint: disable=too-many-statements,too-many-locals
def ansiblelint_main(argv: list[str] | None = None) -> LintResult:
    """Linter CLI entry point (based on ansiblelint/__main__.py)."""
    # alter PATH if needed (venv support)
    path_inject()

    if argv is None:  # pragma: no cover
        argv = sys.argv
    initialize_options(argv[1:])

    console_options["force_terminal"] = options.colored
    reconfigure(console_options)

    initialize_logger(options.verbosity)
    for level, message in log_entries:
        _logger.log(level, message)
    _logger.debug("Options: %s", options)
    _logger.debug("CWD: %s", Path.cwd())

    # pylint: disable=import-outside-toplevel
    from ansiblelint.rules import RulesCollection
    from ansiblelint.runner import get_matches

    app = get_app(offline=None)  # to be sure we use the offline value from settings
    rules = RulesCollection(
        options.rulesdirs,
        profile_name=options.profile,
        app=app,
        options=options,
    )

    if isinstance(options.tags, str):
        options.tags = options.tags.split(",")  # pragma: no cover
    result = get_matches(rules, options)

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
    if options.mock_filters:
        _logger.warning(
            "The following filters were mocked during the run: %s",
            ",".join(options.mock_filters),
        )

    return_code = app.report_outcome(result, mark_as_success=mark_as_success)

    return result, mark_as_success, return_code
