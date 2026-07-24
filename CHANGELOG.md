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
- Generated public professional contact candidate database
- Generated official social-source registry for the website
- Verified LinkedIn organisation pages for AFC, OFC, Concacaf, Canada Soccer, Liga Portugal, and Auckland City FC

### Changed
- Vacancy scope limited to Head Coach and Assistant Coach
- Fitness Coach excluded
- Technical Director excluded
- Coach Education excluded
- Daily operating cadence selected
- Existing maintenance and research workflows changed to manual-only to prevent duplicate schedules
- Existing website now reads the generated pipeline JSON without changing the visual design
- Pipeline configuration pushes trigger one immediate verification run
- Existing Contacts page merges role-based email candidates detected on official pages
- LinkedIn watch is limited to Head Coach and Assistant Coach vacancies and verified coach-change signals
- Fitness Coach summary was removed from the current opportunity view

### Pending
- Review generated contact candidates before using them for applications
- Expand official professional-club website coverage conservatively
- Review gated LinkedIn content manually when login is required
