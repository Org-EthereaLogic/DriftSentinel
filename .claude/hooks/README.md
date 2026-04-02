# .claude/hooks

Claude Code hook handlers and shared utilities for local session logging and
safety checks.

## Files

| File | Purpose |
| --- | --- |
| `pre-tool-use.js` | Logs pre-tool events and blocks dangerous `rm` patterns or non-sample `.env` access |
| `post-tool-use.js` | Appends post-tool events to the current session log |
| `user-prompt-submit.js` | Logs user prompt submissions for the active session |
| `notification.js` | Logs Claude Code notification events |
| `pre-compact.js` | Logs pre-compaction events before context compaction |
| `stop.js` | Logs stop events and persists the main transcript as `chat.json` when available |
| `subagent-stop.js` | Logs subagent stop events and persists subagent transcript as `subagent_chat.json` |
| `utils.js` | Shared helpers for reading stdin and writing session-scoped JSON logs under `logs/hooks/` |

## Notes

- These hooks are operational tooling, not product runtime code.
- Session logs default to `logs/hooks/` unless `CLAUDE_HOOKS_LOG_DIR` overrides
  the destination.
- Hooks are designed to fail open on logging errors so local tooling issues do
  not block the Claude session.
