import pytest
import sys

from ansible_content_parser.__main__ import _run_cli_entrypoint
from unittest import TestCase
from unittest.mock import patch


class TestMain(TestCase):
    def test_cli_without_parameters(self):
        testargs = ["ansible-content-parser"]
        with patch.object(sys, 'argv', testargs):
            with self.assertRaises(SystemExit) as cm:
                _run_cli_entrypoint()

            self.assertEqual(cm.exception.code, 1, 'The exit code should be 1')
