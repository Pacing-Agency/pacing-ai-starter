<p align="center">
  <img src="docs/banner.svg" alt="Pacing: pacing-ai-starter. Safe defaults for AI coding agents." width="100%">
</p>

# pacing-ai-starter

Stop AI coding agents sending email on your behalf, committing API keys, or colliding on the same files: template Cursor rules, a pre-commit secret guard, and a script that makes those rules work in Claude Code too.

[![Tests](https://github.com/Pacing-Agency/pacing-ai-starter/actions/workflows/tests.yml/badge.svg)](https://github.com/Pacing-Agency/pacing-ai-starter/actions/workflows/tests.yml)
[![Licence: MIT](https://img.shields.io/badge/licence-MIT-orange.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

## Who it's for

Anyone setting up Cursor, Claude Code or both on a real repo, especially small teams and agencies where an agent has access to client work, email or chat. You do not need to be a security specialist: copy the files, fill in the placeholders, and you have sensible guardrails.

## What problem it solves

- **Agents act outside the repo.** Without a rule, an agent can send or draft email, or post to Slack, Google Chat or Teams, because it seemed helpful.
- **Credentials end up in commits.** An API key pasted into a script or a `.env` file staged by accident reaches git history. The hook stops it at commit time.
- **Several agents trample each other.** Two tools editing the same files, or one tool picking up another's half-finished job, causes lost work. Lanes give each kind of work one owner.

## Quick start

The rules in `rules/` are Cursor `.mdc` files. Claude Code does not read `.mdc` files, so step 3 uses the parity script to generate the Claude Code copies from them.

```bash
git clone https://github.com/Pacing-Agency/pacing-ai-starter.git
cd /path/to/your-repo

# 1. Rules: copy into your repo and fill in the {{PLACEHOLDERS}}
mkdir -p .cursor/rules
cp ../pacing-ai-starter/rules/*.mdc .cursor/rules/
grep -rn '{{' .cursor/rules

# 2. Secret guard (optional): blocks commits containing credentials
sh ../pacing-ai-starter/hooks/install.sh

# 3. Claude Code: generate its config from .cursor/
cp ../pacing-ai-starter/parity/cursor_claude_parity.py .
python cursor_claude_parity.py .            # generate
python cursor_claude_parity.py . --check    # drift check, exit 1 on drift
```

Python 3.9 or later for the generator, standard library only. Node is only needed for the optional session hook. Adjust the `../pacing-ai-starter` paths to wherever you cloned it.

## What is in the kit

### Six rules (`rules/`)

| Rule | What it does |
|---|---|
| `_project-baseline.mdc` | One short page of house conventions (language, secrets, naming, repo hygiene) that every agent reads first. |
| `no-em-dashes.mdc` | An example house-style rule: small, concrete, checkable. Keep it or swap it for your own. |
| `no-send-email.mdc` | Agents must not send or draft email unless you ask in the current message. |
| `no-send-chat.mdc` | The same for Slack, Google Chat or Teams. |
| `agent-lanes.mdc` | Several AI tools in one repo: one owner per kind of work, handoff through a file, backed by a hook. |
| `oauth-credential-hygiene.mdc` | What to do when an OAuth token fails, tips on scopes, and what never to commit. |

Placeholders are in double braces, for example `{{OWNER_NAME}}`. Where a rule has a table, replace the rows with your own.

### Secret guard (`hooks/`)

`hooks/pre-commit` blocks a commit when an added line looks like a credential, or when `.env`, `*.keys.json`, `*.pem` and similar files are staged. It prints file names, never values. `hooks/install.sh` copies it to `.githooks/pre-commit` and sets `core.hooksPath`. `hooks/session-start-enable-hooks.cjs` is an optional `sessionStart` hook that does the same on every clone.

What it catches:

- Common key shapes: `sk-...`, `ghp_...`, `github_pat_...`, `AKIA...`, Slack `xox*-...`, Google `AIza...`, `-----BEGIN ... PRIVATE KEY-----` blocks and `"refresh_token": "..."` values.
- Assignments to a name containing `api_key`, `api-key`, `apikey`, `secret`, `token` or `password`, in any case, with or without `export`, quoted or unquoted, and in `=`, `:` or JSON form: `api_key = "..."`, `API_KEY=...`, `export SECRET=...`, `"password": "..."`. The value must be 20 or more characters.

What it deliberately lets through: `.env.example`-style placeholders such as `API_KEY=your-key-here` or `API_KEY=` (under the length floor), long values starting with `your`, `example`, `changeme`, `placeholder`, `replace`, `xxx`, `todo` or `<`, and references such as `${API_KEY}` or `os.environ["API_KEY"]`. A real secret shorter than 20 characters will also pass, so it is not a scanner. A long value that is not a secret (for example `token = some.long.config.path`) can trigger a false positive: fix the line or use `git commit --no-verify` once.

Edit the `PATTERNS` or `ASSIGN` line to add your own.

### Parity generator (`parity/`)

`parity/` is a copy of the standalone [cursor-claude-parity](https://github.com/Pacing-Agency/cursor-claude-parity) repo, bundled so the kit works in one clone. If you only need the generator, install the standalone one: it is the same script.

You write rules, agents, skills, MCP servers and hooks once under `.cursor/`. The generator writes the Claude Code side:

| Source | Generated |
|---|---|
| `.cursor/mcp.json` | `.mcp.json` (`${env:VAR}` becomes `${VAR}`, `envFile` dropped, `type` set on URL servers) |
| `.cursor/rules/*.mdc` | `CLAUDE.md` index block, `.claude/rules/*.md` (copies of always-on rules, path-scoped pointers for glob rules) |
| `.cursor/agents/*.md` | `.claude/agents/*.md` (thin pointers, Cursor model slugs dropped) |
| `.cursor/skills/*/SKILL.md` | `.claude/skills/*/SKILL.md` (pointers) |
| `.cursor/hooks.json` | `.claude/settings.json` (event names converted) |

Generated files carry a marker comment. It never overwrites a hand-written file, and only edits the block between the `claude-parity` markers in `CLAUDE.md`. `--check` writes nothing and exits 1 on drift, so use it in CI. Exit codes: 0 fine, 1 drift or conflict, 2 bad arguments, 3 no rules found (override with `--allow-no-rules`).

Why copies for `.mdc` rules: Claude Code only inlines `@` imports of `.md` files, so always-on `.mdc` rules are copied into `.claude/rules/`. `--check` catches a stale copy.

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

### Hooks

Cursor hook events are converted to Claude Code names: `sessionStart` to `SessionStart`, `sessionEnd` to `SessionEnd`, `preToolUse` to `PreToolUse`, `postToolUse` to `PostToolUse`, `beforeSubmitPrompt` to `UserPromptSubmit`. Any other event is not ported, and the script prints a `note:` line naming it. If `.claude/settings.json` already exists and was not generated by this script, hooks are not ported at all and a note says so.

What does not transfer: Cursor marketplace plugins, canvases, Cursor OAuth sessions (remote MCP servers need re-authorising in Claude Code with `/mcp`), and Cursor model slugs in agent files (only `sonnet`, `opus`, `haiku` and `inherit` are kept).

Try it on the bundled example:

```bash
cp -r pacing-ai-starter/parity/examples/tiny-repo /tmp/demo
python pacing-ai-starter/parity/cursor_claude_parity.py /tmp/demo
```

## Limits

- **The secret guard is a safety net, not a scanner.** It checks added lines for common key shapes and suspicious assignments. A real secret shorter than 20 characters passes, and a long value that is not a secret can trigger a false positive (fix the line or use `git commit --no-verify` once). Use gitleaks or trufflehog for history and CI.
- **Rules are advice to an agent, not enforcement.** Only the hook actually blocks anything.
- **Parity is one-way, from Cursor to Claude Code.** There is no pip package; copy the script in.
- **The templates are a starting point.** Replace the placeholders and the example rows with your own.

## Tests

```bash
python -m unittest discover -s parity/tests
python -m unittest discover -s hooks/tests
```

The hook tests run `hooks/pre-commit` on a scratch git repo for each case.

## Contributing

Issues and pull requests are welcome. Keep the scripts standard library only, add a test for any behaviour change, and make sure both test commands above pass.

## Licence

[MIT](LICENSE).

---

Built by [Pacing](https://pacing.agency), a London marketing and build agency. MIT. More on this project: [pacing.agency/built/ai-starter-kit](https://pacing.agency/built/ai-starter-kit).
