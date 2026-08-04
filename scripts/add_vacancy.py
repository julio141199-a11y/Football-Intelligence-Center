#!/usr/bin/env python3
"""Add or update one ChatGPT/Codex-reviewed vacancy JSON file."""

from __future__ import annotations
import argparse
from vacancy_manager import run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    summary = run(files=[__import__("pathlib").Path(args.file)], include_pipeline=False)
    print(summary)
    return 1 if summary["rejected"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
