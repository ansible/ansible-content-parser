"""Generate FT data."""
import json
import logging

from pathlib import Path
from typing import TypedDict

# pylint: disable=import-error
from sage_scan.models import (
    SageObject,
    Task,
    load_objects,
)
from sage_scan.process.utils import get_tasks


_logger = logging.getLogger(__name__)


class _FTRecord(TypedDict):
    data_source_description: str
    input: str
    license: str
    module: str
    output: str
    path: str
    repo_name: str
    repo_url: str


class _FTDataError(Exception):
    pass


def _gen_ftdata(task: Task, parent: SageObject) -> _FTRecord:
    record = _FTRecord(
        data_source_description="",
        input="",
        license="",
        module="",
        output="",
        path="",
        repo_name="",
        repo_url="",
    )

    record["data_source_description"] = task.source.get("data_source_description", "")
    record["license"] = task.source.get("license", "")
    record["module"] = task.module
    record["repo_url"] = task.source.get("repo_url", "")
    record["repo_name"] = task.source.get("repo_name", "")
    record["path"] = task.filepath

    output = ""
    task_name = task.name
    yaml_lines = task.yaml_lines

    # split on the task name to determine the output
    if task_name:
        separator = task_name
        if task_name not in yaml_lines and task_name[-1] == ".":
            separator = task_name[:-1]
        parts = yaml_lines.split(separator)
        if len(parts) >= 2:
            # Remove the trailing spaces and newline characters from name value
            # if they are present after splitting on just the task name
            output = parts[1].lstrip(" ").lstrip("\n")

    # If we don't have an output, then we don't have a valid sample
    if output == "":
        msg = "No output is found."
        raise _FTDataError(msg)

    record["output"] = output

    parent_yaml = parent.yaml_lines

    # Get everything up to and including the prompt as the input
    # if its the first task then
    _input = ""
    task_line_num = task.line_num_in_file[0]
    if task_line_num:
        _input = "\n".join(parent_yaml.splitlines()[:task_line_num])

    # If we don't have an input, then we don't have a valid sample
    if _input == "":
        msg = "No input is found."
        raise _FTDataError(msg)

    record["input"] = _input

    return record


def gen_ftdata_jsonl(sage_objects_json: str, ftdata_jsonl: str) -> None:
    """Generate ftdata.jsonl file."""
    record_lines = []
    for project in load_objects(sage_objects_json).projects():
        parents = []
        if project.playbooks:
            parents.extend(project.playbooks)
        if project.taskfiles:
            parents.extend(project.taskfiles)
        for parent in parents:
            for task in get_tasks(root=parent, project=project):
                try:
                    record = _gen_ftdata(task=task, parent=parent)
                    record_lines.append(json.dumps(record) + "\n")
                except _FTDataError:
                    _logger.debug(
                        "No FT Data was generated for the task:\n"
                        "  (name): %s\n"
                        "  (yaml_lines): %s",
                        task.name,
                        task.yaml_lines,
                    )

    if len(record_lines) == 0:
        _logger.warning("No training data set was created.")
    else:
        with Path(ftdata_jsonl).open("w", encoding="utf-8") as file:
            file.write("".join(record_lines))
