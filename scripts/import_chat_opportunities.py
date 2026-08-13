#!/usr/bin/env python3
"""Backward-compatible alias for import_chat_vacancies.py."""

from __future__ import annotations

from import_chat_vacancies import main


if __name__ == "__main__":
    raise SystemExit(main())
