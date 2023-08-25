"""Produce reports."""
import argparse
import datetime
import json
import sys

from collections import Counter
from pathlib import Path
from typing import TextIO


def filetype_summary(
    result: dict[str, list[dict[str, str]]],
    f: TextIO,
) -> list[tuple[str, int]]:
    """Output the summary table for file types."""
    kinds = {file["filename"]: file["kind"] for file in result["files"]}
    counts = Counter(kinds.values())
    summary = []
    for kind in sorted(counts, key=lambda x: counts[x], reverse=True):
        kind_str = "(file type not identified)" if kind == "" else kind
        summary.append((kind_str, counts[kind]))
        print(f"{kind_str} - {counts[kind]}", file=f)
    return summary


def module_summary(sage_objects_json: str, f: TextIO) -> None:
    """Output the summary table for Ansible modules appeared."""
    modules = []
    with Path(sage_objects_json).open(encoding="utf-8") as lines:
        for line in lines:
            sage_obj = json.loads(line)
            obj_type = sage_obj.get("type")
            if obj_type == "task":
                executable_type = sage_obj.get("executable_type")
                if executable_type == "Module":
                    module = sage_obj.get("module")
                    resolved_name = sage_obj.get("resolved_name")
                    if resolved_name:
                        module = resolved_name
                    modules.append(module)
    module_counts = Counter(modules)
    for module in sorted(module_counts, key=lambda x: module_counts[x], reverse=True):
        print(f"{module} - {module_counts[module]}", file=f)


def report_header(f: TextIO) -> None:
    """Output a formatted report header."""
    time_now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    version = "V0.0.1"
    source_url = "git@github.com:IBM/Ansible-OpenShift-Provisioning.git"
    print(
        f"""**** Ansible Content Parser {version} ****
[ Execution summary ]
Date/Time: {time_now}
Input: {source_url}
        """,
        file=f,
    )


def report(
    file_list: str,
    sarif_file: str,
    sage_objects_json: str,
    report_file: str,
) -> int:
    """Produce a summary report."""
    with Path(report_file).open(
        "w",
        encoding="utf-8",
    ) if report_file else sys.stdout as f:
        report_header(f)

        with Path(file_list).open(encoding="utf-8") as json_f:
            result = json.load(json_f)
            files = result["files"]

        with Path(sarif_file).open(encoding="utf-8") as sarif_f:
            result = json.load(sarif_f)
            matches = result["runs"][0]["results"]

        print("----", file=f)
        print("[ File counts per file type ]", file=f)
        filetype_summary(result, f)

        print("----", file=f)
        print("[ Ansible module counts ]", file=f)
        module_summary(sage_objects_json, f)

        print("----", file=f)
        kinds = {f["filename"]: f["kind"] for f in files}
        for filename in sorted(kinds):
            if (
                kinds[filename] != ""
            ):  # Skip files that was not identified by ansible-lint
                print(f"{filename} - {kinds[filename]}", file=f)

        print("----", file=f)
        print("[ Issues found by ansible-lint ]", file=f)
        for match in matches:
            print(f'Type: {match["ruleId"]}', file=f)
            print(
                f'Path: {match["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]}',
                file=f,
            )
            print(
                f'Line: {match["locations"][0]["physicalLocation"]["region"]["startLine"]}',
                file=f,
            )
            print(f'Description: {match["message"]["text"]}', file=f)
            print(file=f)
        print("----", file=f)

    return 0


def main(argv: list[str]) -> int:
    """Execute report generation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("file_list", help="File list processed by ansible-lint")
    parser.add_argument("sarif_file", help="SARIF JSON output from ansible-lint")
    parser.add_argument("sage_objects_json", help="sage objects")
    parser.add_argument("report_file", nargs="?", default=None, help="report_output")
    args = parser.parse_args(argv)

    if not args.file_list:
        parser.print_help()
        return 1

    return report(
        args.file_list,
        args.sarif_file,
        args.sage_objects_json,
        args.report_file,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
