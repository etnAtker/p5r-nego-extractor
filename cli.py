"""Command-line interface for the negotiation extraction pipeline."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from pipeline import NegotiationPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract P5R negotiation tables from TALK scripts.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing TALK_*.BF.msg/.msg.h/.flow files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory where CSV files will be written.",
    )
    parser.add_argument(
        "--scripts",
        nargs="*",
        default=None,
        help="Optional list of TALK script basenames (e.g. TALK_01JIGAKU). Defaults to auto-discovery.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")

    pipeline = NegotiationPipeline(
        input_dir=args.input_dir.expanduser(),
        output_dir=args.output_dir.expanduser(),
        scripts=args.scripts,
    )
    pipeline.run()


if __name__ == "__main__":
    main()
