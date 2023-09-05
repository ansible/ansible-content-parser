"""A runpy entry point for ansible-content-parser.

This makes it possible to invoke CLI
via :command:`python -m ansible_content_parser`.
"""
import argparse
import contextlib
import errno
import json
import logging
import os
import shutil
import sys
import tarfile
import typing
import zipfile

from collections.abc import Generator
from pathlib import Path

from ansiblelint.constants import RC
from ansiblelint.file_utils import Lintable
from git import Repo

from .lint import ansiblelint_main


_logger = logging.getLogger(__name__)


class LintableDict(dict[str, typing.Any]):
    """The LintableDict class."""

    def __init__(self, lintable: Lintable) -> None:
        """Initialize LintableDict."""
        self["base_kind"] = str(lintable.base_kind)
        self["dir"] = str(lintable.dir)
        self["exc"] = None if lintable.exc is None else str(lintable.exc)
        self["filename"] = str(lintable.filename)
        self["kind"] = str(lintable.kind)
        self["name"] = str(lintable.name)
        self["parent"] = None if lintable.parent is None else str(lintable.parent.name)
        self["role"] = str(lintable.role)
        self["stop_processing"] = bool(lintable.stop_processing)
        self["updated"] = bool(lintable.updated)


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
) -> dict[str, list[LintableDict]]:
    """Execute ansible-lint."""
    with pushd(work_dir):
        result, mark_as_success = ansiblelint_main(argv)
        return {
            "files": [LintableDict(lintable) for lintable in result.files],
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse arguments."""
    parser = argparse.ArgumentParser(description="TODO")
    parser.add_argument(
        "-t",
        "--source-type",
        help="source type",
    )
    parser.add_argument(
        "-r",
        "--repo-name",
        help="repository name",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="explain what is being done",
    )
    parser.add_argument(
        "source",
        help="source, which can be an zip/tar archive, a Git URL or a local directory",
    )
    parser.add_argument(
        "output",
        help="output directory",
    )
    args = parser.parse_args(argv)

    if not args.output:
        parser.print_help()
        sys.exit(1)

    return args


def main(argv: list[str]) -> int:
    """Parse arguments and execute the content parser."""
    args = parse_args(argv)

    prepare_source_and_output(args.source, args.output)

    out_path = Path(args.output)
    sarif_file = str(out_path / "sarif.json")

    argv = ["__DUMMY__", "--sarif-file", sarif_file, "--write"]
    if args.verbose:
        argv.append("-v")

    try:
        serializable_result = execute_ansiblelint(
            argv,
            (Path(args.output) / "repository").as_posix(),
        )
        output_path = Path(args.output)
        if not output_path.exists():
            output_path.mkdir(parents=True)
        with (output_path / "lint-result.json").open("w", encoding="utf-8") as f:
            f.write(json.dumps(serializable_result, indent=2))
    except Exception:
        _logger.exception("An exception was thrown while running ansible-lint.")
        return -1

    return 0


def prepare_source_and_output(source: str, output: str) -> None:
    """Prepare source (archive/url/directory) and output directory."""
    supported_tar_file_extensions = [
        ".tar",
        ".tar.gz",
        ".tgz",
        ".tar.bz2",
        ".tbz2",
        ".tar.xz",
        ".txz",
    ]

    supported_git_url_prefixes = [
        "https://",
        "git@",
    ]

    output_path = setup_output(output)

    # Make sure a subdirectory can be created in the output directory
    repository_path = output_path / "repository"
    repository_path.mkdir()

    # Check if the specified source is a supported archive.
    if source.endswith(".zip"):
        try:
            check_zip_file_is_safe(source)
            with zipfile.ZipFile(source) as zip_file:
                zip_file.extractall(repository_path)
                return
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
                        tar.extractall(repository_path)
                    return
                except Exception:
                    _logger.exception(
                        "An exception thrown in extracting files from %s.",
                        source,
                    )
                    sys.exit(1)

    # Check if the specified source is a URL
    for prefix in supported_git_url_prefixes:
        if source.startswith(prefix):
            try:
                Repo.clone_from(source, repository_path)
                return
            except Exception:
                _logger.exception(
                    "An exception thrown in cloning git repository %s.",
                    source,
                )
                sys.exit(1)

    # Assume the source is a local director
    if Path(source).is_dir():
        repository_path.rmdir()
        shutil.copytree(source, repository_path)
    else:
        _logger.error("%s is not a directory.", source)
        sys.exit(1)


def setup_output(output: str) -> Path:
    """Set up output directory."""
    # Check if the specified output directory exists.
    output_path = Path(output)
    if not output_path.is_dir():
        output_path.mkdir(parents=True)
    # Getting the list of directories
    files = os.listdir(output)
    if len(files) > 0:
        _logger.error("Output directory is not empty.")
        sys.exit(1)
    return output_path


# Ref: https://sonarcloud.io/organizations/ansible/rules?open=python%3AS5042&rule_key=python%3AS5042&tab=how_to_fix
threshold_entries = 10000
threshold_size = 1000000000
threshold_ratio = 10


def check_tar_file_is_safe(source: str) -> None:
    """Make sure that expanding the tar file is safe."""
    total_size_archive = 0
    total_entry_archive = 0

    with tarfile.open(source) as f:  # NOSONAR
        for entry in f:
            tarinfo = f.extractfile(entry)

            total_entry_archive += 1
            size_entry = 0
            while True:
                size_entry += 1024
                total_size_archive += 1024

                ratio = size_entry / entry.size
                # Added the check if entry.size is larger than 1024. When it is very small (like 20 bytes or so)
                # the ratio can exceed the threshold.
                if entry.size > 1024 and ratio > threshold_ratio:
                    msg = "ratio between compressed and uncompressed data is highly suspicious, looks like a Zip Bomb Attack"
                    raise RuntimeError(
                        msg,
                    )

                if tarinfo is None:
                    break
                chunk = tarinfo.read(1024)
                if not chunk:
                    break

            if total_entry_archive > threshold_entries:
                msg = "too much entries in this archive, can lead to inodes exhaustion of the system"
                raise RuntimeError(
                    msg,
                )

            if total_size_archive > threshold_size:
                msg = "the uncompressed data size is too much for the application resource capacity"
                raise RuntimeError(
                    msg,
                )


def check_zip_file_is_safe(source: str) -> None:
    """Make sure that expanding the zip file is safe."""
    total_size_archive = 0
    total_entry_archive = 0

    with zipfile.ZipFile(source, "r") as f:
        for info in f.infolist():
            data = f.read(info)
            total_entry_archive += 1

            total_size_archive = total_size_archive + len(data)
            ratio = len(data) / info.compress_size
            if ratio > threshold_ratio:
                msg = "ratio between compressed and uncompressed data is highly suspicious, looks like a Zip Bomb Attack"
                raise RuntimeError(
                    msg,
                )

            if total_size_archive > threshold_size:
                msg = "the uncompressed data size is too much for the application resource capacity"
                raise RuntimeError(
                    msg,
                )

            if total_entry_archive > threshold_entries:
                msg = "too much entries in this archive, can lead to inodes exhaustion of the system"
                raise RuntimeError(
                    msg,
                )


def _run_cli_entrypoint() -> None:
    """Invoke the main entrypoint with current CLI args.

    This function also processes the runtime exceptions.
    """
    try:
        argv = sys.argv[1:]
        parse_args(argv)
        return_code = main(argv)
        if return_code != 0:
            sys.exit(return_code)
    except OSError as exc:
        # NOTE: Only "broken pipe" is acceptable to ignore
        if exc.errno != errno.EPIPE:  # pragma: no cover
            raise
    except KeyboardInterrupt:  # pragma: no cover
        sys.exit(RC.EXIT_CONTROL_C)
    except RuntimeError as exc:  # pragma: no cover
        raise SystemExit(exc) from exc

    sys.exit(return_code)


if __name__ == "__main__":
    _run_cli_entrypoint()
