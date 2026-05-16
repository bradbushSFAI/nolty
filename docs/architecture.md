# Architecture

## The big picture

```
                    ┌────────────────────────────┐
                    │  ~/Library/LaunchAgents/   │
                    │  com.<rdns>.cron-runner    │ ← macOS launchd
                    │  (every 15 min)            │
                    └────────────┬───────────────┘
                                 │
                                 ▼
            ┌──────────────────────────────────────┐
            │ cron-runner/bin/cron-runner.py       │ ← Python dispatcher
            │  - reads cron-jobs.json              │
            │  - computes due jobs (lag window)    │
            │  - types slash command into tmux     │
            │  - updates cron-state.json           │
            └────────────┬─────────────────────────┘
                         │ tmux send-keys
                         ▼
   ┌─────────────────────────────────────────────────────┐
   │  tmux session: CC_running_like_OC                   │
   │  cwd: nolty/TelegramConfig/                         │
   │                                                     │
   │  ┌────────────────────────────────────────────┐     │
   │  │  claude --channels plugin:telegram@...     │     │
   │  │  --model claude-opus-4-6                   │     │
   │  │  (interactive, NEVER claude -p)            │     │
   │  └─┬──────────────────────────────────────────┘     │
   │    │                                                │
   │    ├─→ reads SOUL/IDENTITY/USER/MEMORY/etc.         │
   │    ├─→ Telegram plugin (bun subprocess)             │
   │    │   ←→ Telegram Bot API                          │
   │    └─→ slash commands                               │
   │         │                                           │
   │         │  if "[cron model:X effort:Y]" suffix:     │
   │         ▼                                           │
   │       ┌─────────────────────────────────────┐       │
   │       │  Task sub-agent (model X, effort Y) │       │
   │       │  - inherits claude-in-chrome MCP    │       │
   │       │  - inherits reply MCP tool          │       │
   │       │  - runs the skill                   │       │
   │       │  - calls reply() to Telegram        │       │
   │       └─────────────────────────────────────┘       │
   └─────────────────────────────────────────────────────┘
```

## Why this design

The architecture solves four constraints simultaneously:

### 1. Single-client Chrome MCP

`claude-in-chrome` can only bond to one Claude session at a time. If you run a headless `claude -p` cron, it can't grab Chrome because the user's interactive session holds it. Solution: NEVER use `claude -p`. The cron-runner types slash commands into the user's existing interactive session.

### 2. No Agent SDK billing (June 15, 2026 split)

`claude -p` draws from the Agent SDK credit pool starting June 15. Interactive Claude Code stays on the standard plan. By keeping everything interactive, the stack never touches the SDK credit pool.

### 3. Main thread must stay responsive to Telegram chat

If a cron job runs in Nolty's main thread, she can't reply to user messages until it finishes. Solution: the cron-suffix dispatch routing rule. When a slash command arrives with `[cron model:X effort:Y]`, Nolty spawns a Task sub-agent and her main thread immediately becomes free again.

### 4. Sub-agents need the same MCPs as the parent

Web-driven crons (LinkedIn) need `claude-in-chrome`. Sub-agents inherit all MCP connections from their parent — including Chrome — so a sub-agent spawned by a cron can scrape LinkedIn using the user's real signed-in Chrome session.

## Failure modes and recovery

| Failure | Symptom | Recovery |
|---|---|---|
| Mac rebooted, LaunchAgent not in `~/Library/LaunchAgents/` | Cron-runner doesn't start back up | Symlink the plist into `~/Library/LaunchAgents/` (install.sh handles this) |
| Claude Code auto-upgraded its binary | Telegram outbound silently fails; bun bridge severed | `/heartbeat` STEP 0.5 detects within 30 min and triggers `clawd-restart.sh` |
| tmux session died | Cron slash commands type into nothing | `/nolty-restart` detects and respawns |
| bun process died but claude still alive | Inbound messages don't arrive | `/nolty-restart` respawns the whole session |
| LaunchAgent loaded but stale (>16 min since fire) | Crons stopped | `/nolty-restart` kickstarts the agent |
| Hard crash (everything down) | Telegram silent for hours | User runs `/nolty-restart` from any Claude Code session |

## Why tmux?

Three reasons:

1. **Persistence across terminal close.** You can `ssh` into your Mac later and the agent is still running.
2. **Inspection.** `tmux attach -t CC_running_like_OC` shows you exactly what Nolty is doing right now.
3. **Programmability.** `tmux send-keys` lets the cron-runner feed slash commands without needing any other RPC channel.

The downside: tmux is single-threaded. While Nolty is running a slow tool call, new Telegram messages queue. The dispatch-to-sub-agent pattern mitigates this — sub-agents do the slow work; the main thread stays free to read inbound chat.

## Why `cron-runner.py` instead of just crontab?

- **JSON config** that Nolty can read and edit programmatically (the `cron-management` skill exists because of this)
- **Single dispatcher process** for all jobs, with shared state (`cron-state.json`)
- **Max-lag logic** to skip stale fires after the Mac sleeps overnight, instead of firing 8 backed-up morning briefs at 9am
- **Atomic state writes** (write to .tmp, rename)

A native crontab can't easily do those things.

## Why TelegramConfig as a subfolder?

The Telegram plugin loads from `.claude/settings.json` in the **workspace root only** — Claude Code doesn't walk up the directory tree. So:

- If `nolty/.claude/settings.json` has plugin enabled, opening `nolty/` in an IDE spawns a Telegram listener inside that IDE's Claude Code session → two listeners → conflict.
- If `nolty/.claude/settings.json` has plugin disabled and `nolty/TelegramConfig/.claude/settings.json` has plugin enabled, the listener only spawns when something explicitly runs from `TelegramConfig/`.

The `clawd-restart.sh` script `cd`s into `TelegramConfig/` before launching claude, so the always-on session loads the plugin. The user can open `nolty/` in an IDE without double-listening.

## File responsibilities at a glance

| File | Role |
|---|---|
| `CLAUDE.md` | Nolty's operating rules — read on every session start |
| `SOUL.md` / `IDENTITY.md` / `USER.md` / `MEMORY.md` / `HEARTBEAT.md` / `AGENTS.md` / `TOOLS.md` | Foundation files — also read every session start |
| `cron-runner/cron-jobs.json` | Cron schedule source of truth |
| `cron-runner/state/cron-state.json` | Runtime state: last_fired_at per job, fire_count, statuses |
| `cron-runner/bin/cron-runner.py` | The dispatcher |
| `clawd-restart.sh` | Restart Nolty's tmux session (the recovery primitive) |
| `~/.claude/commands/nolty-restart.md` | `/nolty-restart` slash command for hard-crash recovery |
| `skills/heartbeat/SKILL.md` | Every-30-min check including version-drift self-heal |
| `skills/cron-management/SKILL.md` | Natural-language CRUD over `cron-jobs.json` |

See [cron-runner-internals.md](cron-runner-internals.md) for the dispatcher's internals.
