# FIC Change Log

## [Unreleased]

### Added
- FIC AI Employee operating-system design
- Project charter
- Agent roles and workflow
- Task board
- Quality gates
- Runnable 08:00 Asia/Seoul daily update workflow
- Generic, fail-safe opportunity collector and pipeline validator
- Starter public-source registry for priority regions and official Instagram accounts
- Generated `data/opportunities.json` and `data/updates.json`

### Changed
- Vacancy scope limited to Head Coach and Assistant Coach
- Fitness Coach excluded
- Technical Director excluded
- Coach Education excluded
- Daily operating cadence selected
- Existing maintenance and research workflows changed to manual-only to prevent duplicate schedules
- Existing website now reads the generated pipeline JSON without changing the visual design

### Pending
- Confirm repository Workflow permissions allow `GITHUB_TOKEN` write access
- Run the workflow once from GitHub Actions
- Confirm the generated JSON is reachable through GitHub Pages
