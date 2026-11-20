# pacing-ai-starter

> Safe defaults for AI coding agents: template Cursor rules, a pre-commit secret guard, and a script that ports the rules to Claude Code.

## What this is

A starter kit you copy into your own repo. It has six template rules (`rules/*.mdc`, with `{{PLACEHOLDERS}}` to fill in), a pre-commit hook that blocks commits containing credentials (`hooks/`), and a bundled copy of the standalone `cursor-claude-parity` generator (`parity/`). Public repo, MIT licence. The README is the user guide.

## Stack

- Python 3.9 or newer, standard library only (the parity script and the tests).
- Shell (`hooks/pre-commit`, `hooks/install.sh`) and one optional Node file (`hooks/session-start-enable-hooks.cjs`).

## Local setup

```bash
python -m unittest discover -s parity/tests
python -m unittest discover -s hooks/tests    # runs hooks/pre-commit on scratch git repos
```

## Deploy

None. Users copy files out of this repo. There is no package to publish.

## Where things live

- `rules/` - the six template rules
- `hooks/` - the secret guard, its installer, the optional session hook and its tests
- `parity/` - bundled `cursor_claude_parity.py`, its tests and `examples/tiny-repo/`
- `docs/` - banner images for the README
- `.github/workflows/tests.yml` - CI

## Gotchas

- `parity/cursor_claude_parity.py` is a copy of the standalone `cursor-claude-parity` repo. Change the generator there first, then copy it here.
- The secret guard prints file names, never values. Never put a real key in a test: build test strings at run time.
- Keep the scripts standard library only, and add a test for any behaviour change. British English, no em dashes.

## Monitoring

Nothing runs on a schedule and there is no service. The only workflow is `tests.yml`, which runs both test commands on every push and pull request (Python 3.9 and 3.13). Nothing else watches this repo.
