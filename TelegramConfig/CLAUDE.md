# TelegramConfig/

This subfolder exists ONLY to scope the Telegram plugin to this directory.

Claude Code reads `.claude/settings.json` from the workspace root only — it doesn't walk up. By putting the Telegram-enabled settings in `TelegramConfig/.claude/settings.json` and the parent `nolty/.claude/settings.json` set to plugin-disabled, you can:

- Run Nolty from `TelegramConfig/` → Telegram plugin loads
- Open the parent `nolty/` in VS Code → no duplicate Telegram listener spawned

The `clawd-restart.sh` script CDs into this directory before launching `claude`.

## On session start

Your real home is the parent directory. Read the parent's `CLAUDE.md` first:

```
/Users/YOUR_USER/Documents/CodingProjects/nolty/CLAUDE.md
```

Everything else (SOUL, IDENTITY, USER, MEMORY, HEARTBEAT, AGENTS, TOOLS, skills/, agents/) lives in the parent. Use relative paths like `../SOUL.md` or absolute paths to reach them.
