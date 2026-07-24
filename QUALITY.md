# FIC Quality Standard

## Scope gate
Only Head Coach and Assistant Coach roles for men's/women's national teams and men's professional clubs.

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
- Separate public facts from Julio fit assessment
- Salary is Not Public unless officially disclosed
- Contacts must be publicly posted for professional use

## Status rules
- Verified Open
- Closing Soon
- To Verify
- Closed
- Filled

## Failure policy
Do not commit invalid data. Preserve the last known-good version and report the exact blocker.

## Pipeline gate
- One generic collector; no country-specific parser.
- A source failure must not stop other sources.
- Interrupted or incomplete HTTP responses must be recorded as warnings and must not stop the run.
- Only Head Coach and Assistant Coach terms may create candidates.
- Automated candidates are always `To Verify`.
- Official social accounts that require authentication remain registry-only.
- Generated opportunities are deduplicated by source URL, role, and organisation.
- Contact collection is limited to public role-based addresses on official organisation pages.
- Automatically detected contacts start as `To Verify`; a reviewed contact may become `Verified` or `Historical` only with a public-source note.
- LinkedIn sources must be official organisation profiles. Do not store personal profiles or claim that gated posts were automatically reviewed.
