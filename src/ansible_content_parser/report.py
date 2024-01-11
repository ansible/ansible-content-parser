"""Generate reports."""
import argparse
import datetime
import json
import logging

from collections import Counter
from pathlib import Path
from typing import TypedDict

from sarif import loader  # pylint: disable=import-error
from sarif.operations import summary_op  # pylint: disable=import-error

from .lintable_dict import LintableDict
from .version import __version__


_logger = logging.getLogger(__name__)

_label_count = "Count"
_label_file_type = "File Type"
_label_file_path = "File Path"
_label_file_state = "Excluded/Autofixed"
_label_module_name = "Module Name"
_label_total = "TOTAL"

_report_txt = "report.txt"


def filetype_summary(result: dict[str, list[LintableDict]]) -> str:
    """Calculate summary stats for file types."""
    kinds = {f["filename"]: f["kind"] for f in result["files"]}
    counts = Counter(kinds.values())
    entries = []
    total = 0
    max_kind_len = len(_label_file_type)
    max_count_len = 0
    for kind in sorted(counts, key=lambda x: counts[x], reverse=True):
        kind_str = "(file type not identified)" if kind == "" else kind
        count = str(counts[kind])
        total += counts[kind]
        entries.append([kind_str, count])
        if len(kind_str) > max_kind_len:
            max_kind_len = len(kind_str)

    max_count_len = max(len(str(total)), len(_label_count))

    num_spaces = 5
    separator = "-" * (max_kind_len + num_spaces + max_count_len)
    summary = separator + "\n"
    summary += (
        _label_file_type.ljust(max_kind_len)
        + " " * num_spaces
        + _label_count.rjust(max_count_len)
        + "\n"
    )
    summary += separator + "\n"
    for kind_str, count in entries:
        summary += (
            kind_str.ljust(max_kind_len)
            + " " * num_spaces
            + count.rjust(max_count_len)
            + "\n"
        )
    summary += separator + "\n"
    summary += (
        _label_total.ljust(max_kind_len)
        + " " * num_spaces
        + str(total).rjust(max_count_len)
        + "\n"
    )
    summary += separator

    return summary


def get_file_list_summary(files: list[LintableDict], excluded_paths: list[str]) -> str:
    """Get summary string from the lintable list."""
    entries = []
    max_filename_len = len(_label_file_path)
    max_kind_len = len(_label_file_type)
    max_state_len = len(_label_file_state)
    kinds = {f["filename"]: f["kind"] for f in files}
    updated = {f["filename"]: f["updated"] for f in files}
    excluded = {f["filename"]: (f["filename"] in excluded_paths) for f in files}
    for filename in sorted(kinds):
        kind = kinds[filename]
        if kind != "":  # Skip files that was not identified by ansible-lint
            state = (
                "excluded"
                if excluded[filename]
                else "autofixed"
                if updated[filename]
                else ""
            )
            entries.append([filename, kind, state])
            if len(filename) > max_filename_len:
                max_filename_len = len(filename)
            if len(kind) > max_kind_len:
                max_kind_len = len(kind)
            if len(state) > max_state_len:
                max_state_len = len(state)

    num_spaces = 2
    separator = "-" * (
        max_filename_len + num_spaces + max_kind_len + num_spaces + max_state_len
    )
    summary = separator + "\n"
    summary += (
        _label_file_path.ljust(max_filename_len)
        + " " * num_spaces
        + _label_file_type.ljust(max_kind_len)
        + " " * num_spaces
        + _label_file_state
        + "\n"
    )
    summary += separator + "\n"
    for filename, kind, state in entries:
        summary += (
            filename.ljust(max_filename_len)
            + " " * num_spaces
            + kind.ljust(max_kind_len)
            + " " * num_spaces
            + state
            + "\n"
        )
    summary += separator

    return summary


def get_sarif_summary(metadata_path: Path, sarif_file: str) -> str:
    """Get summary string from the SARIF JSON file."""
    sarif_summary = metadata_path / "sarif_summary.txt"
    sarif_file_set = loader.load_sarif_files(sarif_file)
    summary_op.generate_summary(sarif_file_set, str(sarif_summary), False)
    with sarif_summary.open(encoding="utf-8") as f:
        summary = f.read()
    sarif_summary.unlink()
    return summary


class _SageObject(TypedDict):
    annotations: dict[str, str]
    module: str
    module_info: dict[str, str]


def get_module_name(o: _SageObject) -> str:
    """Find a module name in a dictionary that represents an Ansible task."""
    module_name = o.get("module", "")
    if not module_name:
        _logger.error("No module name was found in a task: %s", json.dumps(o))
        module_name = "(not found)"
    return module_name


def get_module_summary(sage_objects: str) -> str:
    """Get summary string for Ansible modules found in running the Content Parser."""
    modules = []
    with Path(sage_objects).open(encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            if o.get("py/object") == "sage_scan.models.Task":
                modules.append(get_module_name(o))

    counts = Counter(modules)
    entries = []
    max_module_len = len(_label_module_name)
    total = 0
    for module in sorted(counts, key=lambda x: (-counts[x], x)):
        count = str(counts[module])
        total += counts[module]
        entries.append([module, count])
        if len(module) > max_module_len:
            max_module_len = len(module)

    max_count_len = max(len(str(total)), len(_label_count))

    num_spaces = 5
    separator = "-" * (max_module_len + num_spaces + max_count_len)
    summary = separator + "\n"
    summary += (
        _label_module_name.ljust(max_module_len)
        + _label_count.rjust(max_count_len + num_spaces)
        + "\n"
    )
    summary += separator + "\n"
    for module, count in entries:
        summary += (
            module.ljust(max_module_len)
            + " " * num_spaces
            + count.rjust(max_count_len)
            + "\n"
        )
    summary += separator + "\n"
    summary += (
        _label_total.ljust(max_module_len)
        + " " * num_spaces
        + str(total).rjust(max_count_len)
        + "\n"
    )
    summary += separator
    return summary


def get_excluded_files(excluded: list[str]) -> str:
    """Get the list of excluded files in the second ansible-lint run."""
    max_filename_len = len(_label_file_path)
    for file_path in excluded:
        if len(file_path) > max_filename_len:
            max_filename_len = len(file_path)

    summary = "-" * max_filename_len + "\n"
    summary += _label_file_path + "\n"
    summary += "-" * max_filename_len + "\n"
    for file_path in excluded:
        summary += f"{file_path}\n"
    summary += "-" * max_filename_len + "\n"

    return summary


def generate_report(
    json_file: str,
    json_file2: str,
    sarif_file: str,
    sarif_file2: str,
    args: argparse.Namespace,
    excluded_paths: list[str],
) -> None:
    """Generate report."""
    report = f"""
********************************************************************************
****                Ansible Content Parser Execution Report                 ****
********************************************************************************

Date/Time             : {datetime.datetime.now(tz=datetime.timezone.utc).isoformat()}
Content Parser Version: {__version__}
Source Repository     : {args.source}
Output Directory      : {args.output}
"""
    out_path = Path(args.output)
    metadata_path = out_path / "metadata"

    if json_file:
        with Path(json_file).open(encoding="utf-8") as f:
            result = json.load(f)
            files_all = result["files"]

    last_json_file = json_file2 if json_file2 else json_file
    if last_json_file:
        with Path(last_json_file).open(encoding="utf-8") as f:
            result = json.load(f)
            files = result["files"]
            excluded = result.get("excluded", [])

            # If the "last" JSON file was the one obtained from the second run,
            # it does not contain the information about the excluded files.
            # If it is the case, add those files in the JSON file from the first run.
            if last_json_file != json_file:
                files += [f for f in files_all if f["filename"] in excluded]

        report += f"""

[ File counts per type ]

{filetype_summary(result)}


[ List of Ansible files identified ]

{get_file_list_summary(files, excluded_paths)}


[ Issues found by ansible-lint ]
"""
    if sarif_file2:
        report += f"""
(First run)
{get_sarif_summary(metadata_path, sarif_file)}

(Second run)

- Files excluded from the second run due to syntax-check errors found in the first run

{get_excluded_files(excluded)}
{get_sarif_summary(metadata_path, sarif_file2)}
"""
    else:
        if sarif_file:
            report += f"""
{get_sarif_summary(metadata_path, sarif_file)}
"""
    with (out_path / _report_txt).open(mode="w") as f:
        f.write(report)

    return


def add_module_summary(sage_objects: str, args: argparse.Namespace) -> None:
    """Add Ansible module summary to the report."""
    summary = get_module_summary(sage_objects)

    out_path = Path(args.output)
    report_path = out_path / _report_txt

    with report_path.open(mode="a") as f:
        f.write(
            f"""

[ List of Ansible modules found in tasks ]

{summary}
""",
        )
