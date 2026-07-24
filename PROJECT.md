# Football Intelligence Center — Project Charter

## Mission
Maintain a mobile-first intelligence system that helps Julio Park find, verify, prioritise, and act on realistic overseas football coaching opportunities.

## Scope
Track only:
- Head Coach
- Assistant Coach
- Men's national teams
- Women's national teams
- Men's professional clubs

Exclude:
- Fitness Coach
- Technical Director
- Coach Education
- Sporting Director
- Analyst roles
- Women's professional clubs
- Academy-only roles

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
- Public role-based emails found on official federation, league, and club pages are stored separately as `To Verify`.
- GitHub commits generated files only when they change.
