# FIC Change Log

## [Unreleased]

### Added
- Added 152 current professional-club records across 11 priority Asian markets, using official league or association participant sources and safe public contact routes
- Added a repeatable priority-club contact updater that preserves existing contacts and replaces only its own managed records
- Added the Work/ChatGPT reviewed-vacancy bridge and single import command.
- Added the single `import_chat_vacancies.py` reviewed-input interface with file, inline JSON, and inbox modes.
- Added chat-feed-to-vacancy-to-website integration coverage.
- Added 31 focused AFC/OFC federation decision-maker records sourced from FIFA's official directory
- Added automatic refresh for Technical Directors, General Secretaries, national coaches, and official federation contacts
- Added a decision-maker validator and existing Contacts-page integration without redesign
- Added a standard vacancy database, history, closed archive, and change/error logs
- Added reviewed JSON inbox/import commands and a fail-closed vacancy validator
- Added stable vacancy IDs, source hashes, deduplication, KST deadline states, and unit tests
- Added a small `data/chat_opportunities.json` inbox for vacancies verified from Julio's ChatGPT/Codex conversations
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
- Automatic official-website monitoring for the Malaysia, Singapore, Philippines, Indonesia, New Zealand, and Costa Rica federations
- Stable-operations guide defining daily automation and the limited cases that require manual work
- Pre-Pro career profile based on the AFC Competition Operations Manual 2026

### Changed
- Updated 11 priority country/league licence summaries: Philippines and Chinese Taipei have published AFC A-compatible routes subject to association recognition; the other reviewed domestic markets remain association-confirmation-required
- Marked unverified club-direct email, decision-maker, phone, and social fields as `Not Public` instead of guessing them
- Daily vacancy processing now consumes chat opportunities, reviewed inbox files, and pipeline opportunities together.
- Work/Chat imports now allow only Head Coach and Assistant Coach and fail closed for Fitness Coach and all other roles.
- Vacancy deduplication now checks both stable IDs and source hashes.
- Merged Countries and League & Licence into one essential Countries & Leagues accordion view.
- Grouped Contacts into exclusive continent and country accordions for easier mobile browsing
- Expanded the single daily workflow to 08:00 and 18:00 Asia/Seoul
- Connected standardised vacancy JSON to the existing website and priority view without redesign
- Automatic vacancy commits now include only generated files and occur only after validation
- Connected generated and chat-reviewed opportunities to the existing Jobs page while preserving the current design
- Added cache-bypassed JSON loading so newly deployed vacancy data appears immediately
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
- Incomplete HTTP responses now fail safely without stopping other sources
- Added a concise GitHub Actions summary and no-noise issue alerts for new Head Coach or Assistant Coach candidates only
- Reviewed the first four generated contacts: two verified, one historical, and one still requiring verification
- Verified New Zealand Football careers/general contacts and the FCRF general contact; Singapore recruitment remains pending verification
- Added the verified Philippine Football Federation secretariat, retained its older HR address as historical only, and added Auckland City FC's publicly listed General Manager contact
- Added a small source-access override layer: three access-blocked federation sites now remain manual official registries, while Forge FC and Auckland City use working official pages
- Declared the first FIC daily-automation release feature-complete; future work now prioritises verified applications over additional features
- Prioritised senior national-team Assistant Coach, national U20 Head Coach, and officially verified AFC A-compatible professional-club Head Coach opportunities
- Removed Coach Network from the site and managed databases
- Removed Fitness Coach from live job and League Intelligence filters
- Renamed the user-facing League Intelligence page to League & Licence and clarified that unverified data is not proof of eligibility

### Pending
- Review generated contact candidates before using them for applications
- Expand official professional-club website coverage conservatively
- Review gated LinkedIn content manually when login is required
- Verify and add official LinkedIn profiles for additional priority federations and professional clubs
