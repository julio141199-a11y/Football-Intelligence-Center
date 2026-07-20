# FIC AI Employee Phase 2

This package adds a safe daily maintenance layer.

## What it does automatically
- Runs every day at 08:00 Korea time
- Recalculates `daysUntilDeadline`
- Changes verified open vacancies to `Closing Soon` within three days
- Changes expired open vacancies to `Closed`
- Validates all JSON files
- Checks scope, IDs, statuses, dates, URLs, and probable duplicates
- Commits only when a real deadline-derived change exists

## What it does not do yet
It does not independently search the public web for new vacancies. Reliable web research requires a supported search/API service or a scheduled AI agent with verified GitHub write access. This phase creates the safe repository and QA foundation first.

## Upload
Upload the folders and files to the repository root while preserving paths:
- `.github/workflows/fic-daily-maintenance.yml`
- `config/*`
- `scripts/*`
- `tests/*`
- `requirements.txt`

Then open the Actions tab and run `FIC Daily Maintenance` manually once.
