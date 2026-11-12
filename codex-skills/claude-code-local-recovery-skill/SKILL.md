---
name: claude-code-local-recovery
description: Audit, back up, and restore local Claude Code sessions after switching Claude accounts. Use when Claude/Claude Code account access changes, the user wants old Code-mode chats to appear in Claude Desktop again, `claude --resume` can see sessions but the desktop UI cannot, or Codex needs to migrate/fill `~/.claude/projects` and Claude Desktop `claude-code-sessions` indexes safely.
---

# Claude Code Local Recovery

Use this skill to reconnect a new Claude account to local Claude Code history without treating it as a cloud-chat migration.

## Safety Rules

- Back up before writing. Never delete `~/.claude`, `~/.claude.json`, or Claude Desktop indexes.
- Default to audit/dry-run. Only mutate when the user explicitly asks to apply changes.
- Treat `~/.claude.json` and session transcripts as sensitive. Do not upload or paste them.
- Do not copy large project folders to recover chat lists. Desktop Code chats depend on indexes, not project file duplication.
- Always use quoted paths. Many user paths contain spaces.
- Restart Claude Desktop after index changes.

## Mental Model

Claude Code recovery has two local layers:

1. Raw transcript layer: `~/.claude/projects/**/*.jsonl`
   - Used by `claude --resume`.
   - Survives account changes if the machine and files remain.
2. Desktop Code sidebar/index layer: `~/Library/Application Support/Claude/claude-code-sessions/<accountUuid>/<organizationUuid>/*.json`
   - Used by Claude Desktop Code mode.
   - Changes when the logged-in account/organization changes.

If terminal resume works but Desktop Code chats are missing, the raw layer is intact and the desktop index layer needs migration or regeneration.

## Workflow

1. Confirm the user wants local Code-mode recovery, not claude.ai cloud chat migration.
2. Run an audit:

```bash
python scripts/audit_state.py --project-prefix "/Users/example/Documents/claude code安装"
```

3. If needed, set long retention in `~/.claude/settings.json`:

```json
{
  "cleanupPeriodDays": 3650
}
```

4. Validate raw transcripts manually from a project directory:

```bash
cd "/path/to/project"
claude --resume
```

5. Dry-run desktop index sync:

```bash
python scripts/sync_desktop_index.py \
  --project-prefix "/path/to/project-root" \
  --source-index-dir "/old/account/org/index" \
  --dry-run
```

6. Apply only after user approval:

```bash
python scripts/sync_desktop_index.py \
  --project-prefix "/path/to/project-root" \
  --source-index-dir "/old/account/org/index" \
  --apply
```

7. Quit and reopen Claude Desktop, then open the specific project folder in Code mode.

## Choosing Directories

- Target index defaults to the currently logged-in account from `~/.claude.json` when possible.
- Source index is the old account/org folder under `~/Library/Application Support/Claude/claude-code-sessions`.
- Project prefix should be the parent whose project sessions should show in Desktop Code, for example `/Users/example/Documents/claude code安装`.
- Open specific project folders in Claude Desktop; the UI is organized by each session's `cwd`, not by a full parent-folder tree.

## Resources

- `scripts/audit_state.py`: read-only report of raw transcripts, desktop index folders, current account, and missing index entries.
- `scripts/sync_desktop_index.py`: copy existing desktop indexes and generate missing index entries from raw transcripts. Dry-run by default.
- `references/recovery_model.md`: extra reference for troubleshooting and explaining the workflow to users.
