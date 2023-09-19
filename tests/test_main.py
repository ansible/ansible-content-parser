"""Test __main__.py."""
import argparse
import contextlib
import json
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


# pylint: disable=import-error
from ansible_content_parser.__main__ import (
    get_project_root,
    main,
    update_argv,
)


sample_playbook = """---
- name: Apache server installed
  hosts: web

  post_tasks:
  # Edge case: a (post) task without name
  - meta: clear_facts

  tasks:
  - name: latest Apache version installed
    yum:
      name: httpd
      state: latest

  - name: latest firewalld version installed
    yum:
      name: firewalld
      state: latest

  - name: firewalld enabled and running
    service:
      name: firewalld
      enabled: true
      state: started

  - name: firewalld permits http service
    firewalld:
      service: http
      permanent: true
      state: enabled
      immediate: yes

  # Edge case: a task with a two-line name
  - name: "Apache enabled and \
running"
    service:
      name: httpd
      enabled: true
      state: started
"""

galaxy_yml = """namespace: "namespace_name"
name: "collection_name"
version: "1.0.12"
readme: "README.md"
authors:
    - "Author1"
    - "Author2 (https://author2.example.com)"
    - "Author3 <author3@example.com>"
license:
    - "MIT"
tags:
    - demo
    - collection
repository: "https://www.github.com/my_org/my_collection"
description: Sample description
"""

dot_ansible_lint = """---
# .ansible-lint
profile: basic
verbosity: 1
"""

sample_playbook_name = "playbook.yml"
galaxy_yml_name = "galaxy.yml"
dot_ansible_lint_name = ".ansible-lint"
repo_name = "repo_name"


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

    def create_repo(self, source: TemporaryDirectory[str]) -> None:
        """Create a playbook YAML file."""
        with (Path(source.name) / sample_playbook_name).open("w") as f:
            f.write(sample_playbook)
        with (Path(source.name) / galaxy_yml_name).open("w") as f:
            f.write(galaxy_yml)
        with (Path(source.name) / dot_ansible_lint_name).open("w") as f:
            f.write(dot_ansible_lint)

    def create_tarball(
        self,
        source: TemporaryDirectory[str],
        compression: str = "",
    ) -> None:
        """Create a tarball."""
        self.create_repo(source)
        os.chdir(source.name)
        filename = (
            f"{repo_name}.tar.{compression}" if compression else f"{repo_name}.tar"
        )
        mode = f"w:{compression}" if compression else "w"
        with tarfile.open(filename, mode) as tar:
            tar.add(sample_playbook_name)
            tar.add(galaxy_yml_name)
            tar.add(dot_ansible_lint_name)

    def create_zip_file(self, source: TemporaryDirectory[str]) -> None:
        """Create a ZIP file."""
        self.create_repo(source)
        os.chdir(source.name)
        with zipfile.ZipFile(
            f"{repo_name}.zip",
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zip_file:
            zip_file.write(sample_playbook_name)
            zip_file.write(galaxy_yml_name)
            zip_file.write(dot_ansible_lint_name)

    def test_cli_with_local_directory(self) -> None:
        """Run the CLI with a local directory."""
        with temp_dir() as source:
            self.create_repo(source)
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    "-v",
                    source.name + "/",  # intentionally add "/" to the end
                    output.name,
                ]
                with patch.object(sys, "argv", testargs), self.assertRaises(
                    SystemExit,
                ) as context:
                    main()

                assert context.exception.code == 0, "The exit code should be 0"

                with (Path(output.name) / "report.txt").open("r") as f:
                    for line in f:
                        if line == "Module Name     Count\n":
                            line = f.readline()
                            assert line == "---------------------\n"
                            line = f.readline()
                            assert line == "service             2\n"
                            line = f.readline()
                            assert line == "yum                 2\n"
                            line = f.readline()
                            assert line == "firewalld           1\n"
                            line = f.readline()
                            assert line == "meta                1\n"
                            line = f.readline()
                            assert line == "---------------------\n"
                            line = f.readline()
                            assert line == "TOTAL               6\n"
                            line = f.readline()
                            assert line == "---------------------\n"

    def test_cli_with_non_archive_file(self) -> None:
        """Run the CLI with specifying a non archive file as input."""
        with temp_dir() as source:
            self.create_repo(source)
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    (Path(source.name) / sample_playbook_name).as_posix(),
                    output.name,
                ]
                with patch.object(sys, "argv", testargs):
                    with self.assertRaises(SystemExit) as context:
                        main()

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
                    main()

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
                    main()

                assert context.exception.code == 1, "The exit code should be 1"

    def test_cli_with_no_output_specified(self) -> None:
        """Run the CLI without specifying output."""
        with temp_dir() as source:
            testargs = ["ansible-content-parser", source.name]
            with patch.object(sys, "argv", testargs):
                with self.assertRaises(SystemExit) as context:
                    main()

                assert context.exception.code == 2, "The exit code should be 2"

    def test_cli_with_tarball(self) -> None:
        """Run the CLI with a tarball."""
        with temp_dir() as source:
            self.create_tarball(source)
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    "--profile",
                    "min",
                    (Path(source.name) / f"{repo_name}.tar").as_posix(),
                    output.name,
                ]
                with patch.object(sys, "argv", testargs):
                    with self.assertRaises(SystemExit) as context:
                        main()

                    assert context.exception.code == 0, "The exit code should be 0"

    def test_cli_with_compressed_tarball(self) -> None:
        """Run the CLI with a tarball (.tar.gz)."""
        with temp_dir() as source:
            self.create_tarball(source, "gz")
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    "--config-file",
                    source.name + "/" + dot_ansible_lint_name,
                    "--source-license",
                    "Apache",
                    "--source-description",
                    "This is a repo for test",
                    "--repo-name",
                    "test_repo",
                    "--repo-url",
                    "https://repo.example.com/test_repo",
                    str(Path(source.name) / f"{repo_name}.tar.gz"),
                    output.name,
                ]
                with patch.object(sys, "argv", testargs):
                    with self.assertRaises(SystemExit) as context:
                        main()

                    assert context.exception.code == 0, "The exit code should be 0"

                with (Path(output.name) / "ftdata.json").open("r") as f:
                    for line in f:
                        o = json.loads(line)
                        assert o["data_source_description"] == "This is a repo for test"
                        assert o["repo_name"] == "test_repo"
                        assert o["repo_url"] == "https://repo.example.com/test_repo"
                        assert o["license"] == "Apache"

    def test_cli_with_invalid_tarball(self) -> None:
        """Run the CLI with an invalid tarball."""
        with temp_dir() as source:
            self.create_zip_file(source)
            (Path(source.name) / f"{repo_name}.zip").rename(
                str(Path(source.name) / f"{repo_name}.tar"),
            )
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    str(Path(source.name) / f"{repo_name}.tar"),
                    output.name,
                ]
                with patch.object(sys, "argv", testargs):
                    with self.assertRaises(SystemExit) as context:
                        main()

                    assert context.exception.code == 1, "The exit code should be 1"

    def test_cli_with_non_existent_tarball(self) -> None:
        """Run the CLI with a non-existent tarball."""
        with temp_dir() as source, temp_dir() as output:
            testargs = [
                "ansible-content-parser",
                (Path(source.name) / f"{repo_name}.tar").as_posix(),
                output.name,
            ]
            with patch.object(sys, "argv", testargs):
                with self.assertRaises(SystemExit) as context:
                    main()

                assert context.exception.code == 1, "The exit code should be 1"

    def test_cli_with_zip_file(self) -> None:
        """Run the CLI with a zip file."""
        with temp_dir() as source:
            self.create_zip_file(source)
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    (Path(source.name) / f"{repo_name}.zip").as_posix(),
                    output.name,
                ]
                with patch.object(sys, "argv", testargs):
                    with self.assertRaises(SystemExit) as context:
                        main()

                    assert context.exception.code == 0, "The exit code should be 0"

    def test_cli_with_invalid_zip_file(self) -> None:
        """Run the CLI with an invalid zip file."""
        with temp_dir() as source:
            self.create_tarball(source, "gz")
            (Path(source.name) / f"{repo_name}.tar.gz").rename(
                str(Path(source.name) / f"{repo_name}.zip"),
            )
            with temp_dir() as output:
                testargs = [
                    "ansible-content-parser",
                    str(Path(source.name) / f"{repo_name}.zip"),
                    output.name,
                ]
                with patch.object(sys, "argv", testargs):
                    with self.assertRaises(SystemExit) as context:
                        main()

                    assert context.exception.code == 1, "The exit code should be 1"

    def test_cli_with_non_existent_zip_file(self) -> None:
        """Run the CLI with a non-existent zip file."""
        with temp_dir() as source, temp_dir() as output:
            testargs = [
                "ansible-content-parser",
                (Path(source.name) / f"{repo_name}.zip").as_posix(),
                output.name,
            ]
            with patch.object(sys, "argv", testargs):
                with self.assertRaises(SystemExit) as context:
                    main()

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
                    main()

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
                    main()

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
                    main()

                assert context.exception.code == 1, "The exit code should be 1"

    def test_update_argv(self) -> None:
        """Test __main__.update_argv()."""
        input_data = {
            "skip_transform": True,
            "verbose": True,
            "config_file": "config.file",
            "profile": "basic",
        }
        args = argparse.Namespace(**input_data)
        argv = ["__DUMMY__"]
        update_argv(argv, args)

        assert "--write=all" not in argv
        assert "-v" in argv
        assert "--config-file" in argv
        assert "config.file" in argv
        assert "--profile" in argv
        assert "basic" in argv

        input_data = {
            "skip_transform": False,
            "verbose": False,
            "config_file": None,
            "profile": None,
        }
        args = argparse.Namespace(**input_data)
        argv = ["__DUMMY__"]
        update_argv(argv, args)

        assert "--write=all" in argv
        assert "-v" not in argv
        assert "--config-file" not in argv
        assert "--profile" not in argv

    def test_get_project_root(self) -> None:
        with temp_dir() as output:
            output_path = Path(output.name)
            repository_path = output_path / "repository"
            repository_path.mkdir()

            # When there is no file/directory in repository_path,
            # get_project_root return repository_path
            path = get_project_root(repository_path)
            assert path.name == repository_path.name

            # When there is one single directory in repository_path,
            # get_project_root return the directory path
            project_path = repository_path / "project"
            project_path.mkdir()
            path = get_project_root(repository_path)
            assert path.name == project_path.name

            # When there are more than one directories in repository_path,
            # get_project_root return repository_path
            project_path2 = repository_path / "project2"
            project_path2.mkdir()
            path = get_project_root(repository_path)
            assert path.name == repository_path.name
