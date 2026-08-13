#!/usr/bin/env python3
"""Import every JSON vacancy file from a directory."""

from __future__ import annotations
import argparse
from pathlib import Path
from vacancy_manager import run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default="data/inbox")
    args = parser.parse_args()
    files = sorted(Path(args.directory).glob("*.json"))
    summary = run(files=files, include_pipeline=False, include_chat=False)
    print(summary)
    return 1 if summary["rejected"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
