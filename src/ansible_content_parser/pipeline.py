"""Execute pipelines for generating training data."""

import argparse
import logging
import os

from pathlib import Path

from .gen_ftdata import gen_ftdata_jsonl
from .report import add_module_summary


_logger = logging.getLogger(__name__)


def run_pipeline(args: argparse.Namespace, repository_path: Path) -> int:
    """Execute pipelines for generating training data (ftdata.json)."""
    out_path = Path(args.output).absolute()
    metadata_path = out_path / "metadata"

    report_path = out_path / "report.txt"
    ftdata_path = out_path / "ftdata.jsonl"
    lint_result_path = metadata_path / "lint-result.json"
    sage_objects_path = metadata_path / "sage-objects.json"

    if args.verbose:
        os.environ["SAGE_LOG_LEVEL"] = "debug"

    # Note: SagePipeline in imported here because of the way it initializes
    # logging, ansible-lint will generate duplicated log lines if it is
    # imported at the top-level.

    # pylint: disable=import-error,import-outside-toplevel
    from sage_scan.pipeline import (
        SagePipeline,
    )

    dp = SagePipeline()

    dp.run(
        target_dir=str(repository_path),
        lint_result=str(lint_result_path),
        output_dir=str(metadata_path),
        source={
            "data_source_description": args.source_description,
            "license": args.source_license,
            "repo_name": args.repo_name,
            "repo_url": args.repo_url,
        },
    )

    # Generate FT Data
    gen_ftdata_jsonl(
        str(sage_objects_path),
        str(ftdata_path),
    )
    _logger.info("Training data set was created at %s.", str(ftdata_path))

    # Add module section to the report
    add_module_summary(str(sage_objects_path), args)
    _logger.info("Execution report was generated at %s.", str(report_path))

    return 0
