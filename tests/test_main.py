"""Test __main__.py."""
import sys

from unittest import TestCase
from unittest.mock import patch

from ansible_content_parser.__main__ import _run_cli_entrypoint


class TestMain(TestCase):
    """The TestMain class."""

    def test_cli_without_parameters(self) -> None:
        """Run the CLI without parameters."""
        testargs = ["ansible-content-parser"]
        with patch.object(sys, "argv", testargs):
            with self.assertRaises(SystemExit) as context:
                _run_cli_entrypoint()

            assert context.exception.code == 1, "The exit code should be 1"