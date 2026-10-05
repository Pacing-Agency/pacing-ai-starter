#!/usr/bin/env node
/**
 * Optional sessionStart hook: if the repo has .githooks/pre-commit and git has no
 * hooksPath set, point it there. Idempotent, silent, fails open so it never
 * blocks a session. Wire it in .cursor/hooks.json under "sessionStart".
 */
const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

try {
  const root = path.resolve(__dirname, "../..");
  if (fs.existsSync(path.join(root, ".githooks", "pre-commit"))) {
    let current = "";
    try {
      current = execFileSync("git", ["config", "--get", "core.hooksPath"], { cwd: root }).toString().trim();
    } catch {
      /* unset */
    }
    if (!current) execFileSync("git", ["config", "core.hooksPath", ".githooks"], { cwd: root });
  }
} catch {
  /* never block a session */
}
// Cursor hooks expect JSON on stdout; Claude Code hooks do not.
if (!process.argv.includes("--claude")) process.stdout.write("{}");
