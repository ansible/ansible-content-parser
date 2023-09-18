"""Test safe checks for tar/zip files."""
import os
import random
import string
import zipfile

from pathlib import Path
from unittest import TestCase

from ansible_content_parser.safe_checks import check_zip_file_is_safe

from .test_main import sample_playbook, temp_dir


class TestSafeChecks(TestCase):
    """The TestSafeChecks class."""

    def test_with_highly_compressed_zip(self) -> None:
        """Test with a highly compressed zip file."""
        with temp_dir() as source:
            os.chdir(source.name)
            with Path("a.txt").open("w", encoding="utf-8") as f:
                f.write("A" * 4096)
            with zipfile.ZipFile(
                "test.zip",
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as zip_file:
                zip_file.write("a.txt")
            with self.assertRaises(RuntimeError) as context:
                check_zip_file_is_safe("test.zip")

            assert (
                context.exception.args[0]
                == "ratio between compressed and uncompressed data is highly suspicious, looks like a Zip Bomb Attack"
            )

    def test_with_zip_with_too_many_files(self) -> None:
        """Test with a zip file that contains too many files."""
        with temp_dir() as source:
            os.chdir(source.name)
            with Path("0.yml").open("w", encoding="utf-8") as f:
                f.write(sample_playbook)
            with zipfile.ZipFile(
                "test.zip",
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as zip_file:
                for i in range(10001):
                    zip_file.write(f"{i}.yml")
                    Path(f"{i}.yml").rename(f"{i+1}.yml")
            with self.assertRaises(RuntimeError) as context:
                check_zip_file_is_safe("test.zip")

            assert (
                context.exception.args[0]
                == "too many entries in this archive, can lead to inodes exhaustion of the system"
            )

    def test_with_zip_too_big(self) -> None:
        """Test with a zip file that is too big."""
        with temp_dir() as source:
            os.chdir(source.name)
            with Path("0.txt").open("w", encoding="utf-8") as f:
                f.write(sample_playbook)
                random_string = "".join(
                    random.choices(string.ascii_letters, k=1024),
                )
                f.write(random_string * 100)

            with zipfile.ZipFile(
                "test.zip",
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as zip_file:
                for i in range(10000):
                    zip_file.write(f"{i}.txt")
                    Path(f"{i}.txt").rename(f"{i+1}.txt")
            with self.assertRaises(RuntimeError) as context:
                check_zip_file_is_safe("test.zip")

            assert (
                context.exception.args[0]
                == "the uncompressed data size is too much for the application resource capacity"
            )
