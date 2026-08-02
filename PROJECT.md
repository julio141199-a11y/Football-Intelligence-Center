# Football Intelligence Center — Project Charter

## Mission
Maintain a mobile-first intelligence system that helps Julio Park find, verify, prioritise, and act on realistic overseas football coaching opportunities.

## Scope
Track only:
- Head Coach
- Assistant Coach
- Men's national teams
- Women's national teams
- Men's and women's national U20 teams
- Men's professional clubs

Exclude:
- Fitness Coach
- Technical Director
- Coach Education
- Sporting Director
- Analyst roles
- Women's professional clubs
- Academy-only roles
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
- `.github/workflows/daily-update.yml` runs at 08:00 Asia/Seoul (`0 23 * * *` UTC).
- Pipeline code or source-registry changes also trigger one verification run after push.
- `run_pipeline.py` checks a small registry of generic public sources.
- Automated discoveries remain `To Verify`; they are never promoted directly into `jobs.json`.
- Official Instagram accounts are registry-only because reliable automated access requires platform authentication.
- Official LinkedIn organisation profiles are published as a focused watch list. Gated post content remains a manual check; only Head Coach and Assistant Coach hiring or coach-change signals are relevant.
- Public role-based emails found on official federation, league, and club pages are stored separately as `To Verify`.
- GitHub commits generated files only when they change.
- The website merges `jobs.json`, generated `data/opportunities.json`, and Codex-reviewed `data/chat_opportunities.json` without changing the visual template.
- GitHub Actions cannot read a private ChatGPT conversation directly. When Julio asks Codex to publish a chat-discovered vacancy, Codex must verify its public source, add it to `data/chat_opportunities.json`, and push the reviewed change.

## Current lifecycle

FIC is feature-complete for its first stable daily-operation release. See `OPERATIONS.md`.
Further work should focus on verified opportunities, high-value contacts, and application preparation rather than adding features.

## Pre-Pro career priorities

Until Julio obtains the AFC Pro Diploma:

1. Senior national-team Assistant Coach
2. National U20 Head Coach
3. Men's professional-club Head Coach only where official domestic or competition rules accept AFC A or an approved equivalent

The AFC 2026 competition minimum confirms AFC A for senior national-team Assistant Coaches and national U20 Head Coaches. It does not automatically prove eligibility for every domestic first division; each federation, league, club-licensing rule, and recognition process must be checked.
