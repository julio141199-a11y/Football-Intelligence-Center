# Football Intelligence Center — Project Charter

## Mission
Maintain a mobile-first intelligence system that helps Julio Park find, verify, prioritise, and act on realistic overseas football coaching opportunities.

## Scope
Track only:
- Head Coach
- Assistant Coach
- Men's national teams
- Women's national teams
- Men's and women's U23/U20 national teams
- Men's professional clubs

Exclude:
- Technical Director
- Sporting Director
- Analyst roles
- Performance Analyst
- Scout
- Women's professional clubs
- Academy-only roles
- Coach Education by default
- Coach Network

## Priority regions
AFC, Oceania, Portugal, Canada, selected Africa, Central America, the Caribbean, and realistic Europe Watch markets.

## Principles
- Facts before volume
- Official sources first
- Mobile-first and simple
- Preserve good existing data
- No rumours presented as verified
- No redesign unless requested
- Every meaningful change must be traceable

## Definition of success
Relevant opportunities are found early, verified, deduplicated, safely committed, published without breaking GitHub Pages, and reported only when useful.

## Daily automation
- `.github/workflows/daily-update.yml` runs at 08:00 and 18:00 Asia/Seoul (`0 23 * * *` and `0 9 * * *` UTC).
- Pipeline code or source-registry changes also trigger one verification run after push.
- `run_pipeline.py` checks a small registry of generic public sources.
- Automated discoveries remain `To Verify`; they are never promoted directly into `jobs.json`.
- Official Instagram accounts are registry-only because reliable automated access requires platform authentication.
- Official LinkedIn organisation profiles are published as a focused watch list. Gated post content remains a manual check; only Head Coach and Assistant Coach hiring or coach-change signals are relevant.
- Public role-based emails found on official federation, league, and club pages are stored separately as `To Verify`.
- GitHub commits generated files only when they change.
- The website merges `jobs.json`, generated `data/opportunities.json`, Codex-reviewed `data/chat_opportunities.json`, and standardised `data/vacancies.json` without changing the visual template.
- GitHub Actions cannot read a private ChatGPT conversation directly. When Julio asks Codex to publish a chat-discovered vacancy, Codex must verify its public source, add it to `data/chat_opportunities.json`, and push the reviewed change.

## Standard vacancy update

- `scripts/vacancy_manager.py` accepts the reviewed `data/chat_opportunities.json` feed, reviewed JSON from `data/inbox/`, and pipeline candidates.
- `scripts/import_chat_vacancies.py --file reviewed.json` is the single Work/ChatGPT bridge command. It also accepts `--json` and `--inbox`, validates and upserts the reviewed feed, then rebuilds `data/vacancies.json`.
- Every record has a stable ID and source hash; unchanged records are not rewritten as updates.
- Deadlines are evaluated in Asia/Seoul and use `NEW`, `UPDATED`, `CLOSING_SOON`, `CLOSED`, `EXPIRED`, or `UNVERIFIED`.
- Invalid roles, placeholder links, and missing organisation/country fields are rejected before publishing.

## Decision-maker intelligence

- FIFA official member-association pages refresh public federation email, phone, president, General Secretary, Technical Director, and national-team coach records.
- Priority coverage is the 20 requested AFC markets and all 11 FIFA-member OFC associations.
- Northern Mariana Islands is retained as a separate AFC research record because it is not a FIFA member.
- Contacts are professional public routes only. FIC never stores private contact information and always asks the federation to confirm the correct CV recipient.

## Current lifecycle

FIC is feature-complete for its first stable daily-operation release. See `OPERATIONS.md`.
Further work should focus on verified opportunities, high-value contacts, and application preparation rather than adding features.

## Pre-Pro career priorities

Until Julio obtains the AFC Pro Diploma:

1. Senior national-team Assistant Coach
2. National U20 Head Coach
3. Men's professional-club Head Coach only where official domestic or competition rules accept AFC A or an approved equivalent

The AFC 2026 competition minimum confirms AFC A for senior national-team Assistant Coaches and national U20 Head Coaches. It does not automatically prove eligibility for every domestic first division; each federation, league, club-licensing rule, and recognition process must be checked.
