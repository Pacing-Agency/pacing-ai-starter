# pacing-ai-starter

Starter kit for running AI coding agents on a repo without surprises. Two parts that work together:

1. **`rules/` and `hooks/`**: template Cursor rules and a secret-guard pre-commit hook.
2. **`parity/`**: a generator that turns your `.cursor/` set-up into Claude Code config, so one rule set serves both tools.

## Quick start

```bash
# 1. Rules: copy into your repo and fill in the {{PLACEHOLDERS}}
mkdir -p .cursor/rules
cp path/to/pacing-ai-starter/rules/*.mdc .cursor/rules/
grep -rn '{{' .cursor/rules

# 2. Secret guard (optional): blocks commits containing credentials
sh path/to/pacing-ai-starter/hooks/install.sh

# 3. Claude Code: generate its config from .cursor/
cp path/to/pacing-ai-starter/parity/cursor_claude_parity.py .
python cursor_claude_parity.py .            # generate
python cursor_claude_parity.py . --check    # drift check, exit 1 on drift
```

Python 3.9 or later for the generator, standard library only. Node is only needed for the optional session hook.

## Rules (`rules/`)

| Rule | Why it exists |
|---|---|
| `_project-baseline.mdc` | One short page of house conventions (language, secrets, naming, repo hygiene) that every agent reads first. |
| `no-em-dashes.mdc` | An example of a house-style rule: small, concrete, checkable. Keep it or swap it for your own. |
| `no-send-email.mdc` | Agents must not send or draft email unless you ask in the current message. Stops surprise outbound mail. |
| `no-send-chat.mdc` | The same for Slack, Google Chat or Teams. |
| `agent-lanes.mdc` | If several AI tools share a repo, give each kind of work one owner and hand off through a file. Says how to back it with a hook. |
| `oauth-credential-hygiene.mdc` | What to do when an OAuth token fails, tips on scopes, and what never to commit. |

Placeholders are in double braces, for example `{{OWNER_NAME}}`. Where a rule has a table, replace the rows with your own.

## Secret guard (`hooks/`)

`hooks/pre-commit` blocks a commit when an added line looks like a credential, or when `.env`, `*.keys.json`, `*.pem` and similar files are staged. It prints file names, never values.

What it catches:

- Common key shapes: `sk-...`, `ghp_...`, `github_pat_...`, `AKIA...`, Slack `xox*-...`, Google `AIza...`, `-----BEGIN ... PRIVATE KEY-----` blocks and `"refresh_token": "..."` values.
- Assignments to a name containing `api_key`, `api-key`, `apikey`, `secret`, `token` or `password`, in any case, with or without `export`, quoted or unquoted, and in `=`, `:` or JSON form: `api_key = "..."`, `API_KEY=...`, `export SECRET=...`, `"password": "..."`. The value must be 20 or more characters.

What it deliberately lets through: `.env.example`-style placeholders such as `API_KEY=your-key-here` or `API_KEY=` (under the length floor), long values starting with `your`, `example`, `changeme`, `placeholder`, `replace`, `xxx`, `todo` or `<`, and references such as `${API_KEY}` or `os.environ["API_KEY"]`. A real secret shorter than 20 characters will also pass, so it is not a scanner. A long value that is not a secret (for example `token = some.long.config.path`) can trigger a false positive: fix the line or use `git commit --no-verify` once.

Tests: `python -m unittest discover -s hooks/tests` runs the hook on a scratch git repo for each case.

Edit the `PATTERNS` or `ASSIGN` line to add your own.

`hooks/install.sh` copies it to `.githooks/pre-commit` and sets `core.hooksPath`. `hooks/session-start-enable-hooks.cjs` is an optional `sessionStart` hook that does the same on every clone.

It is a safety net, not a scanner. Use gitleaks or trufflehog for history and CI.

## Parity generator (`parity/`)

You write rules, agents, skills, MCP servers and hooks once under `.cursor/`. The generator writes the Claude Code side:

| Source | Generated |
|---|---|
| `.cursor/mcp.json` | `.mcp.json` (`${env:VAR}` becomes `${VAR}`, `envFile` dropped, `type` set on URL servers) |
| `.cursor/rules/*.mdc` | `CLAUDE.md` index block (always-on rules and a "read when" table), `.claude/rules/*.md` (copies of always-on rules, path-scoped pointers for glob rules) |
| `.cursor/agents/*.md` | `.claude/agents/*.md` (thin pointers, Cursor model slugs dropped) |
| `.cursor/skills/*/SKILL.md` | `.claude/skills/*/SKILL.md` (pointers) |
| `.cursor/hooks.json` | `.claude/settings.json` (event names converted) |

Generated files carry a marker comment. It never overwrites a hand-written file, and only edits the block between the `claude-parity` markers in `CLAUDE.md`. `--check` writes nothing and exits 1 on drift, so use it in CI.

Exit codes: 0 fine, 1 drift or conflict, 2 bad arguments, 3 no rules found (override with `--allow-no-rules`).

### Hooks

Cursor hook events are converted to Claude Code names: `sessionStart` to `SessionStart`, `sessionEnd` to `SessionEnd`, `preToolUse` to `PreToolUse`, `postToolUse` to `PostToolUse`, `beforeSubmitPrompt` to `UserPromptSubmit`. Any other event is not ported, and the script prints a `note:` line naming it. If `.claude/settings.json` already exists and was not generated by this script, hooks are not ported at all and a note says so.

### What does not transfer

Cursor marketplace plugins, canvases, Cursor OAuth sessions (remote MCP servers need re-authorising in Claude Code with `/mcp`), and Cursor model slugs in agent files (only `sonnet`, `opus`, `haiku` and `inherit` are kept). The generated block in `CLAUDE.md` says the same.

### Options

All optional. Put them in `.cursor-claude-parity.json` at the repo root, pass `--config FILE`, or use flags.

| Config key | Flag | What it does |
|---|---|---|
| `env_defaults` | `--env-default NAME=VALUE` | Public default for `${env:NAME}`, written `${NAME:-VALUE}`. Never for secrets. |
| `lane_note` | `--lane-note TEXT` | Sentence prefixed to agent descriptions so Claude Code does not start agents you want Cursor to own. |
| `shared_agent_prefixes` | `--shared-agent-prefix P` | Agents starting with `P` skip the lane note. |
| `claude_flag_hooks` | `--flag-hook TEXT` | Hook commands containing `TEXT` get `--claude` appended. |
| `skip_hooks` | `--skip-hook TEXT` | Hook commands containing `TEXT` are not ported. |
| `hook_matchers` | none | `[{"contains": "x.cjs", "matcher": "Edit\|Write"}]` sets a PreToolUse matcher. |
| `claude_template` | `--claude-template PATH` | Starting `CLAUDE.md` for repos with none. |
| `gitignore_lines` | none | Lines ensured in `.gitignore`. |

### Example

`parity/examples/tiny-repo/` is a made-up repo with `.cursor/` only:

```bash
cp -r parity/examples/tiny-repo /tmp/demo && python parity/cursor_claude_parity.py /tmp/demo
```

Before, `.cursor/mcp.json`: `"Authorization": "Bearer ${env:DOCS_TOKEN}"`.
After, `.mcp.json`: `"Authorization": "Bearer ${DOCS_TOKEN}"` and `"type": "http"`.

Before, an agent with `model: claude-sonnet-4` and "Use proactively after a PR is opened."
After, `.claude/agents/reviewer.md`: model slug dropped, lane note first, body is a pointer to `.cursor/agents/reviewer.md`.

Why copies for `.mdc` rules: Claude Code only inlines `@` imports of `.md` files, so always-on `.mdc` rules are copied into `.claude/rules/`. `--check` catches a stale copy.

### Tests

```bash
python -m unittest discover -s parity/tests
```

## Licence

MIT. From [Pacing Agency](https://pacing.agency).
