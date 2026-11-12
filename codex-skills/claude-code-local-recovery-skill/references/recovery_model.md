# Claude Code Local Recovery Model

## What Can Be Recovered

- Local Claude Code transcripts in `~/.claude/projects`.
- Claude Desktop Code-mode chat cards if their index JSON exists or can be regenerated.
- Local skills, settings, hooks, and MCP configuration if the corresponding files remain.

## What Is Not Recovered

- claude.ai cloud chat sidebar entries for another personal account.
- Cloud Projects or Artifacts tied to the old account.
- Organization permissions disabled by the account admin.

## Common Failure Modes

- `loggedIn: true` but Claude Code cannot run: the organization may have disabled subscription access.
- `claude --resume` works but Desktop Code is empty: regenerate or copy desktop indexes.
- Chat cards appear mixed under a parent folder: open the concrete project directory; sessions are keyed by `cwd`.
- Paths fail in terminal: quote paths with spaces.
- Old sessions disappear later: increase `cleanupPeriodDays` and keep backups.

## Minimum Backup Set

- `~/.claude`
- `~/.claude.json`
- `~/Library/Application Support/Claude/claude-code-sessions`
- Project `.claude/`, `CLAUDE.md`, and `.mcp.json` when present
