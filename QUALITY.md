# FIC Quality Standard

## Scope gate
Only Head Coach and Assistant Coach roles for men's or women's national teams and men's professional clubs. Women's professional clubs and academy-only roles are excluded.

## Source gate
Official sources are preferred. Store the source URL. Do not label uncertain information as verified.

## Data gate
- Valid JSON
- Unique IDs
- ISO dates: YYYY-MM-DD
- Preserve unrelated records
- Update lastChecked only after a real check
- No contradictory status and deadline

## Duplicate gate
Organisation + team + role + vacancy period matching indicates a probable duplicate even when wording differs.

## Accuracy gate
- Do not infer licence recognition without evidence
- Do not infer domestic first-division eligibility from an AFC competition minimum; verify domestic and club-licensing rules separately.
- Separate public facts from Julio fit assessment
- Salary is Not Public unless officially disclosed
- Contacts must be publicly posted for professional use

## Status rules
- `NEW`: newly accepted verified input
- `UPDATED`: a meaningful source field changed
- `CLOSING_SOON`: verified deadline is within seven calendar days in Asia/Seoul
- `CLOSED`: official closure was supplied
- `EXPIRED`: verified deadline has passed
- `UNVERIFIED`: automated candidate awaiting human verification

## Failure policy
Do not commit invalid data. Preserve the last known-good version and report the exact blocker.

## Pipeline gate
- One generic collector; no country-specific parser.
- A source failure must not stop other sources.
- Interrupted or incomplete HTTP responses must be recorded as warnings and must not stop the run.
- Repeated access blocks may be moved to registry-only monitoring through the small operational override file; never bypass an official site's access controls.
- Operational URL overrides must reference an existing source ID and remain limited to a small set of confirmed fixes.
- Only Head Coach and Assistant Coach terms may create candidates.
- Automated candidates are always `To Verify`.
- Official social accounts that require authentication remain registry-only.
- Generated opportunities are deduplicated by source URL, role, and organisation.
- Contact collection is limited to public role-based addresses on official organisation pages.
- Automatically detected contacts start as `To Verify`; a reviewed contact may become `Verified` or `Historical` only with a public-source note.
- LinkedIn sources must be official organisation profiles. Do not store personal profiles or claim that gated posts were automatically reviewed.
- Notifications are allowed only for newly detected Head Coach or Assistant Coach candidates and must label them `To Verify`.
- Chat-discovered vacancies require a public source URL and the same two-role scope gate before entering `data/chat_opportunities.json`.
- The browser must load vacancy JSON with cache bypassing so a successful GitHub Pages deployment displays the latest data.
- The standard vacancy validator must pass before automatic commit.
- An unchanged source hash must not create a duplicate or false update.
- Placeholder URLs and all roles other than Head Coach and Assistant Coach must fail closed.
- Technical Director, Sporting Director, Analyst, Coach Education, women's professional-club, and academy-only vacancies must fail closed.
- Federation decision-maker records must come from FIFA, AFC/OFC, or the association's official site.
- Store only public professional contacts; never infer or discover private personal addresses.
- A named decision-maker is not automatically permission to send a CV. Use the official association route and confirm the intended recipient.
- A current official participant list may create a club record, but it does not prove a club-direct email, decision-maker, Instagram account, or AFC A recognition.
- When no club-direct public contact is verified, publish the official league/association route and label the direct contact `Not Public`.
- Never infer domestic Head Coach eligibility from Transfermarkt, a coach's current licence, or an AFC continental competition minimum.
