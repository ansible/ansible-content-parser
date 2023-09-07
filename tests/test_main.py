"""Test __main__.py."""
import contextlib
import os
import sys
import tarfile
import zipfile

from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch

import git

from ansible_content_parser.__main__ import _run_cli_entrypoint


@contextlib.contextmanager
def temp_dir() -> Generator[TemporaryDirectory[str], None, None]:
    """Provide context with a temporary directory."""
    temp_directory = TemporaryDirectory()
    try:
        os.chdir(temp_directory.name)
        yield temp_directory
    finally:
        temp_directory.cleanup()


class TestMain(TestCase):
    """The TestMain class."""

    def create_playbook(self, source: TemporaryDirectory[str]) -> None:
        """Create a playbook YAML file."""
        with (Path(source.name) / "a.yml").open("w") as f:
            f.write("---\nname: test\nhosts: all\n")

    def create_tarball(
        self,
        source: TemporaryDirectory[str],
        compression: str = "",
    ) -> None:
        """Create a tarball."""
        self.create_playbook(source)
        os.chdir(source.name)
        filename = f"a.tar.{compression}" if compression else "a.tar"
        mode = f"w:{compression}" if compression else "w"
        with tarfile.open(filename, mode) as tar:
            tar.add("a.yml")

    def create_zip_file(self, source: TemporaryDirectory[str]) -> None:
        """Create a ZIP file."""
        self.create_playbook(source)
        os.chdir(source.name)
        with zipfile.ZipFile("a.zip", "w") as zip_file:
            zip_file.write("a.yml")

    def test_cli_with_local_directory(self) -> None:
        """Run the CLI with a local directory."""
        with temp_dir() as source:
            self.create_playbook(source)
            with temp_dir() as output:
                testargs = ["ansible-content-parser", source.name, output.name]
                with patch.object(sys, "argv", testargs), self.assertRaises(
                    SystemExit,
                ) as context:
                    _run_cli_entrypoint()

                assert context.exception.code == 0, "The exit code should be 0"

    def test_cli_with_non_archive_file(self) -> None:
        """Run the CLI with specifying a non archive file as input."""
        with temp_dir() as source:
            self.create_playbook(source)
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    (Path(source.name) / "a.yml").as_posix(),
                    output.name,
                ]
                with patch.object(sys, "argv", testargs):
                    with self.assertRaises(SystemExit) as context:
                        _run_cli_entrypoint()

                    assert context.exception.code == 1, "The exit code should be 1"

    def test_cli_with_non_existent_directory(self) -> None:
        """Run the CLI with specifying a non-existent directory as input."""
        with temp_dir() as source, temp_dir() as output:
            testargs = [
                "ansible-content-parser",
                (Path(source.name) / "non_existent_dir").as_posix(),
                output.name,
            ]
            with patch.object(sys, "argv", testargs):
                with self.assertRaises(SystemExit) as context:
                    _run_cli_entrypoint()

                assert context.exception.code == 1, "The exit code should be 1"

    def test_cli_with_non_empty_output_dir(self) -> None:
        """Run the CLI with a non-empty output directory."""
        with temp_dir() as source, temp_dir() as output:
            # Create a file in the output directory
            with (Path(output.name) / "b.yml").open("w") as f:
                f.write("---\nname: test\nhosts: all\n")

            testargs = ["ansible-content-parser", source.name, output.name]
            with patch.object(sys, "argv", testargs):
                with self.assertRaises(SystemExit) as context:
                    _run_cli_entrypoint()

                assert context.exception.code == 1, "The exit code should be 1"

    def test_cli_with_tarball(self) -> None:
        """Run the CLI with a tarball."""
        with temp_dir() as source:
            self.create_tarball(source)
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    (Path(source.name) / "a.tar").as_posix(),
                    output.name,
                ]
                with patch.object(sys, "argv", testargs):
                    with self.assertRaises(SystemExit) as context:
                        _run_cli_entrypoint()

                    assert context.exception.code == 0, "The exit code should be 0"

    def test_cli_with_compressed_tarball(self) -> None:
        """Run the CLI with a tarball (.tar.gz)."""
        with temp_dir() as source:
            self.create_tarball(source, "gz")
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    str(Path(source.name) / "a.tar.gz"),
                    output.name,
                ]
                with patch.object(sys, "argv", testargs):
                    with self.assertRaises(SystemExit) as context:
                        _run_cli_entrypoint()

                    assert context.exception.code == 0, "The exit code should be 0"

    def test_cli_with_non_existent_tarball(self) -> None:
        """Run the CLI with a non-existent tarball."""
        with temp_dir() as source, temp_dir() as output:
            testargs = [
                "ansible-content-parser",
                (Path(source.name) / "a.tar").as_posix(),
                output.name,
            ]
            with patch.object(sys, "argv", testargs):
                with self.assertRaises(SystemExit) as context:
                    _run_cli_entrypoint()

                assert context.exception.code == 1, "The exit code should be 1"

    def test_cli_with_zip_file(self) -> None:
        """Run the CLI with a zip file."""
        with temp_dir() as source:
            self.create_zip_file(source)
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    (Path(source.name) / "a.zip").as_posix(),
                    output.name,
                ]
                with patch.object(sys, "argv", testargs):
                    with self.assertRaises(SystemExit) as context:
                        _run_cli_entrypoint()

                    assert context.exception.code == 0, "The exit code should be 0"

    def test_cli_with_non_existent_zip_file(self) -> None:
        """Run the CLI with a non-existent zip file."""
        with temp_dir() as source, temp_dir() as output:
            testargs = [
                "ansible-content-parser",
                (Path(source.name) / "a.zip").as_posix(),
                output.name,
            ]
            with patch.object(sys, "argv", testargs):
                with self.assertRaises(SystemExit) as context:
                    _run_cli_entrypoint()

                assert context.exception.code == 1, "The exit code should be 1"

    @patch("git.Repo.clone_from")
    def test_cli_with_git_https_url(self, mock_clone_from: MagicMock) -> None:
        """Run the CLI with a git HTTPS URL."""
        mock_clone_from.return_value = None
        with temp_dir() as output:
            testargs = [
                "ansible-content-parser",
                "https://github.com/ansible/ansible-tower-samples.git",
                output.name,
            ]
            with patch.object(sys, "argv", testargs):
                with self.assertRaises(SystemExit) as context:
                    _run_cli_entrypoint()

                assert context.exception.code == 0, "The exit code should be 0"

    @patch("git.Repo.clone_from")
    def test_cli_with_git_ssh_url(self, mock_clone_from: MagicMock) -> None:
        """Run the CLI with a git SSH URL."""
        mock_clone_from.return_value = None
        with temp_dir() as output:
            testargs = [
                "ansible-content-parser",
                "git@github.com:ansible/ansible-tower-samples.git",
                output.name,
            ]
            with patch.object(sys, "argv", testargs):
                with self.assertRaises(SystemExit) as context:
                    _run_cli_entrypoint()

                assert context.exception.code == 0, "The exit code should be 0"

    @patch("git.Repo.clone_from")
    def test_cli_with_non_existent_git_https_url(
        self,
        mock_clone_from: MagicMock,
    ) -> None:
        """Run the CLI with a non-existent HTTPS git URL."""
        mock_clone_from.side_effect = git.GitCommandError("clone")
        with temp_dir() as output:
            testargs = [
                "ansible-content-parser",
                "https://github.com/ansible/non-existent-samples.git",
                output.name,
            ]
            with patch.object(sys, "argv", testargs):
                with self.assertRaises(SystemExit) as context:
                    _run_cli_entrypoint()

                assert context.exception.code == 1, "The exit code should be 1"
