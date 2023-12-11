"""A runpy entry point for ansible-content-parser.

This makes it possible to invoke CLI
via :command:`python -m ansible_content_parser`.
"""
import argparse
import contextlib
import copy  # pylint: disable=preferred-module
import errno
import json
import logging
import os
import shutil
import sys
import tarfile
import zipfile

from collections.abc import Generator
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import giturlparse  # pylint: disable=import-error

from ansiblelint.constants import RC
from git import Repo
from packaging.version import Version

from .lint import ansiblelint_main
from .lintable_dict import LintableDict
from .pipeline import run_pipeline
from .report import generate_report
from .safe_checks import check_tar_file_is_safe, check_zip_file_is_safe
from .version import __version__


_logger = logging.getLogger(__name__)


# https://stackoverflow.com/questions/6194499/pushd-through-os-system
@contextlib.contextmanager
def pushd(new_dir: str) -> Generator[None, None, None]:
    """Use this in a with block to run some operations from a given directory."""
    previous_dir = Path.cwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


def execute_ansiblelint(
    argv: list[str],
    work_dir: str,
) -> tuple[dict[str, list[Any]], int]:
    """Execute ansible-lint."""
    with pushd(work_dir):
        # Clear root logger handlers as ansible-lint adds one without checking existing ones.
        logging.getLogger().handlers.clear()

        result, mark_as_success, return_code = ansiblelint_main(argv)
        return {
            "files": [LintableDict(lintable) for lintable in result.files],
        }, return_code


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse arguments."""
    parser = argparse.ArgumentParser(
        description="Parse Ansible files in the given repository by running ansible-lint and generate"
        " a training dataset for Ansible Lightspeed.",
    )
    parser.add_argument(
        "--config-file",
        help=" Specify the configuration file to use for ansible-lint.  "
        "By default it will look for '.ansible-lint', '.config/ansible-lint.yml', or '.config/ansible-lint.yaml' "
        "in the source repository.",
    )
    parser.add_argument(
        "--profile",
        choices=["min", "basic", "moderate", "safety", "shared", "production"],
        help="Specify which rules profile to be used for ansible-lint",
    )
    parser.add_argument(
        "--fix",
        dest="write_list",  # This is how this option is stored in ansible_lint.
        # default="all", <-- Commented out because this does not work as expected.
        help="Specify how ansible-lint performs auto-fixes, including YAML reformatting. "
        "You can limit the effective rule transforms (the 'write_list') by passing a "
        "keywords 'all' (=default) or 'none' or a comma separated list of rule ids or "
        "rule tags.",
    )
    parser.add_argument(
        "-S",
        "--skip-ansible-lint",
        action="store_true",
        help="Skip the execution of ansible-lint.",
    )
    parser.add_argument(
        "--no-exclude",
        action="store_true",
        help="Do not let ansible-content-parser to generate training dataset by "
        "excluding files that caused lint errors. With this option specified, "
        "a single lint error terminates the execution without generating the "
        "training dataset.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Explain what is being done",
    )
    parser.add_argument(
        "--source-license",
        default="",
        help="Specify the license that will be included in the training dataset.",
    )
    parser.add_argument(
        "--source-description",
        default="",
        help="Specify the description of the source that will be included in the training dataset.",
    )
    parser.add_argument(
        "--repo-name",
        default="",
        help="Specify the repository name that will be included in the training dataset. "
        "If it is not specified, it is generated from the source name.",
    )
    parser.add_argument(
        "--repo-url",
        default="",
        help="Specify the repository url that will be included in the training dataset. "
        "If it is not specified, it is generated from the source name.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=get_version(),
    )
    parser.add_argument(
        "source",
        help="source, which can be an zip/tar archive, a git URL or a local directory",
    )
    parser.add_argument(
        "output",
        help="output directory",
    )
    args = parser.parse_args(argv)
    args.output = str(Path(args.output).absolute())

    if args.config_file:
        args.config_file = str(Path(args.config_file).absolute())

    return args


def set_repo_name_and_repo_url(args: argparse.Namespace, is_file: bool) -> None:
    """Set repository name and URL from source name when they are not set explicitly."""
    if not args.repo_name:
        repo_name = args.source
        if repo_name.endswith("/"):
            repo_name = repo_name[:-1]
        i = repo_name.rfind("/")
        if i != -1:
            repo_name = repo_name[i + 1 :]
        i = repo_name.find(".")
        if i != -1:
            repo_name = repo_name[:i]
        args.repo_name = repo_name

    if not args.repo_url:
        args.repo_url = (
            Path(args.source).absolute().as_uri() if is_file else args.source
        )


def prepare_source_and_output(args: argparse.Namespace) -> Path:
    """Prepare source (archive/url/directory) and output directory."""
    source, output = args.source, args.output

    supported_tar_file_extensions = [
        ".tar",
        ".tar.gz",
        ".tgz",
        ".tar.bz2",
        ".tbz2",
        ".tar.xz",
        ".txz",
    ]

    out_path = setup_output(output)
    repository_path = out_path / "repository"
    metadata_path = out_path / "metadata"

    # Check if the specified source is a supported archive.
    if source.endswith(".zip"):
        try:
            check_zip_file_is_safe(source)
            with zipfile.ZipFile(source) as zip_file:
                repository_path.mkdir()
                zip_file.extractall(repository_path)
                metadata_path.mkdir()
                set_repo_name_and_repo_url(args, True)
                return get_project_root(repository_path)
        except Exception:
            _logger.exception(
                "An exception thrown in extracting files from %s.",
                source,
            )
            sys.exit(1)
    else:
        for ext in supported_tar_file_extensions:
            if source.endswith(ext):
                try:
                    check_tar_file_is_safe(source)
                    with tarfile.open(source) as tar:  # NOSONAR
                        repository_path.mkdir()
                        tar.extractall(repository_path)
                        metadata_path.mkdir()
                        set_repo_name_and_repo_url(args, True)
                    return get_project_root(repository_path)
                except Exception:
                    _logger.exception(
                        "An exception thrown in extracting files from %s.",
                        source,
                    )
                    sys.exit(1)

    # Check if the specified source is a URL
    if giturlparse.validate(source):
        try:
            repository_path.mkdir()
            Repo.clone_from(source, repository_path)
            metadata_path.mkdir()
            set_repo_name_and_repo_url(args, False)
            return repository_path
        except Exception:
            _logger.exception(
                "An exception thrown in cloning git repository %s.",
                source,
            )
            sys.exit(1)

    # Assume the source is a local directory
    if Path(source).is_dir():
        # As shutil.copytree creates repository_path, we do not need to call repository_path,mkdir()
        shutil.copytree(source, repository_path)
        metadata_path.mkdir()
        set_repo_name_and_repo_url(args, True)
    else:
        _logger.error("%s is not a directory.", source)
        sys.exit(1)

    return repository_path


def setup_output(output: str) -> Path:
    """Set up output directory."""
    # Check if the specified output directory exists.
    out_path = Path(output)
    if not out_path.is_dir():
        out_path.mkdir(parents=True)

    # Make sure the directory is empty.
    files = os.listdir(output)
    if len(files) > 0:
        _logger.error("Output directory is not empty.")
        sys.exit(1)

    return out_path


def get_project_root(repository_path: Path) -> Path:
    """Get the project root directory from the given path."""
    files = os.listdir(repository_path)
    # If the given path contains a single directory at root assume it as the project root directory.
    if len(files) == 1:
        path = Path(repository_path / files[0])
        return path if path.is_dir() else repository_path
    return repository_path


def main() -> None:
    """Invoke the main entrypoint with current CLI args.

    This function also processes the runtime exceptions.
    """
    return_code = 0
    try:
        args = parse_args(sys.argv[1:])
        repository_path = prepare_source_and_output(args)

        out_path = Path(args.output)
        metadata_path = out_path / "metadata"

        sarif_file = str(metadata_path / "sarif.json")
        argv = ["ansible-lint", "--sarif-file", sarif_file]
        update_argv(argv, args)

        try:
            execute_lint_step(args, argv, metadata_path, repository_path, sarif_file)
        except Exception:
            _logger.exception("An exception was thrown while running ansible-lint.")
            sys.exit(1)

        return_code = run_pipeline(args, repository_path)

    except OSError as exc:
        # NOTE: Only "broken pipe" is acceptable to ignore
        if exc.errno != errno.EPIPE:  # pragma: no cover
            raise
    except KeyboardInterrupt:  # pragma: no cover
        _logger.info("Terminated by a keyboard interrupt.")
        sys.exit(RC.EXIT_CONTROL_C)
    except RuntimeError:  # pragma: no cover
        raise

    sys.exit(return_code)


def get_version() -> str:
    """Return version string that contains versions of important dependents."""
    msg = f"ansible-content-parser {__version__} using"
    for k in ["ansible-lint", "ansible-core", "sage-scan"]:
        try:
            v = Version(version(k))
            msg += f" {k}:{v}"
        except PackageNotFoundError:
            msg += f" {k}:(not found)"
    return msg


def execute_lint_step(
    args: argparse.Namespace,
    argv: list[str],
    metadata_path: Path,
    repository_path: Path,
    sarif_file: str,
) -> None:
    """Execute ansible-lint and create metadata files."""
    exclude_paths: list[str] = []

    lint_result = ""
    lint_result2 = ""
    sarif_file2 = ""
    return_code = RC.SUCCESS

    if args.skip_ansible_lint:
        sarif_file = ""
    else:
        serializable_result, return_code = execute_ansiblelint(
            argv,
            str(repository_path),
        )
        lint_result = str(metadata_path / "lint-result.json")
        with Path(lint_result).open(
            "w",
            encoding="utf-8",
        ) as f:
            f.write(json.dumps(serializable_result))

        if return_code == RC.SUCCESS or not args.no_exclude:
            exclude_paths = parse_sarif_json(exclude_paths, sarif_file, True)

            # If syntax-errors occurred on some files, kick off the second run excluding those files
            if len(exclude_paths) > 0:
                lint_result2 = str(metadata_path / "lint-result-2.json")
                sarif_file2 = str(metadata_path / "sarif-2.json")
                argv = ["ansible-lint", "--sarif-file", sarif_file2]
                argv.append("--exclude")
                argv.extend(exclude_paths)
                update_argv(argv, args)
                _logger.info(",".join(argv))
                serializable_result_2, return_code = execute_ansiblelint(
                    argv,
                    str(repository_path),
                )
                # create a shallow copy of exclude_paths because the following parse_sarif_json() call
                # will add more files to the list.
                serializable_result_2["excluded"] = copy.copy(exclude_paths)
                exclude_paths = parse_sarif_json(exclude_paths, sarif_file2, False)

                with Path(lint_result2).open(mode="w", encoding="utf-8") as f:
                    f.write(json.dumps(serializable_result_2))
            else:
                exclude_paths = parse_sarif_json(exclude_paths, sarif_file, False)

            if len(exclude_paths) > 0:
                # Rename excluded files to have __EXCLUDED__ extension so that they won't be processed by sage
                _rename_excluded_files(exclude_paths, repository_path)
                _logger.warning(
                    "Following files are excluded from training set generation due to ansible-lint rule "
                    "violations: %s",
                    ",".join(exclude_paths),
                )

    generate_report(
        lint_result,
        lint_result2,
        sarif_file,
        sarif_file2,
        args,
        exclude_paths,
    )

    if return_code != RC.SUCCESS and args.no_exclude:
        msg = "One or more lint errors were found by ansible-lint"
        raise RuntimeError(msg)


def _rename_excluded_files(exclude_paths: list[str], repository_path: Path) -> None:
    with pushd(str(repository_path)):
        for p in exclude_paths:
            path = Path(p)
            # Do not attempt to rename directories (e.g. role names)
            if path.is_file():
                Path(p).rename(p + ".__EXCLUDED__")


def parse_sarif_json(
    exclude_paths: list[str],
    sarif_file: str,
    syntax_check_errors_only: bool,
) -> list[str]:
    """Analyze SARIF.json to see if syntax-check errors occurred or not on the first run."""
    with Path(sarif_file).open("rb") as f:
        o = json.load(f)
        for run in o["runs"]:
            for result in run["results"]:
                if (
                    result["ruleId"].startswith("syntax-check")
                    or not syntax_check_errors_only
                    and ("level" not in result or result["level"] == "error")
                ):
                    exclude_paths.extend(
                        [
                            location["physicalLocation"]["artifactLocation"]["uri"]
                            for location in result["locations"]
                        ],
                    )
    return sorted(set(exclude_paths))


def update_argv(argv: list[str], args: argparse.Namespace) -> None:
    """Update arguments to ansible-lint based on arguments given to ansible-content-parser."""
    if getattr(args, "write_list", None) is None:
        argv.append("--fix=all")
    else:
        argv.append(f"--fix={args.write_list}")
    if args.verbose:
        argv.append("-v")
    if args.config_file:
        argv.append("--config-file")
        argv.append(args.config_file)
    if args.profile:
        argv.append("--profile")
        argv.append(args.profile)


if __name__ == "__main__":
    main()
