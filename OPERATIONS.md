# FIC Stable Operations

## Normal operation

FIC is now in stable daily-operation mode.

- GitHub Actions runs every day at 08:00 and 18:00 Asia/Seoul.
- The pipeline checks the approved lightweight source set.
- The pipeline refreshes the focused AFC/OFC federation decision-maker directory from FIFA official pages.
- Only Head Coach and Assistant Coach candidates are accepted within the PROJECT.md organisation scope.
- Before AFC Pro, target senior national-team Assistant Coach, national U20 Head Coach, and officially verified AFC A-compatible men's professional-club Head Coach roles.
- New candidates remain `To Verify`.
- Generated data is committed and published only after validation passes.
- A GitHub Issue alert is created only when a new target-role candidate is detected.

Julio does not need to run the pipeline or request another development phase each day.

## Manual action is required only when

1. A real candidate alert is created.
2. A contact or licence requirement needs human verification.
3. GitHub Actions reports a failed run.
4. Julio wants to add or remove a priority market or official source.
5. CV, portfolio, cover letter, or application preparation is required.
6. A domestic league's AFC A recognition or club-licensing rule needs verification.

## Weekly check

Open the public FIC site and confirm:

- Last scan is recent.
- No unresolved target-role candidate is waiting.
- Verified contacts remain appropriate before use.

## Monthly check

- Review broken or registry-only official sources.
- Remove obsolete contacts and expired opportunities.
- Add only a small number of high-value official sources.

## Development completion rule

Do not add another feature unless it directly increases Julio Park's chance of obtaining a Head Coach or Assistant Coach interview. Routine data collection belongs to automation, not continued development.

## Add a vacancy found in Work, ChatGPT, or Codex

GitHub Actions cannot read a private chat. Codex must first verify the public source, then use the single reviewed-input bridge:

```sh
python scripts/import_chat_vacancies.py --file reviewed.json
python scripts/import_chat_vacancies.py --inbox
python scripts/validate_vacancies.py
```

Inline JSON is also accepted with `--json`. Successful inbox files move to `data/inbox/processed/`; rejected records are not published and are logged. The scheduled workflow processes the reviewed feed, inbox, and lightweight pipeline automatically.
