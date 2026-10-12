// Demo session-start hook. The generator appends --claude when run under Claude Code
// (see claude_flag_hooks in .cursor-claude-parity.json).
const underClaude = process.argv.includes("--claude");
console.log(underClaude ? "hello from Claude Code" : "hello from Cursor");
