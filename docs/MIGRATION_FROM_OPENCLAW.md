# Migration from OpenClaw

If you're coming from OpenClaw (OC), here's how the concepts map.

## High-level

| OpenClaw | Nolty (Claude Code) |
|---|---|
| `openclaw` daemon process | `claude --channels plugin:telegram@...` running inside a tmux session |
| `oc cron add` / cron table in OC DB | `cron-runner/cron-jobs.json` + `cron-management` skill |
| `oc skill add` / skills stored in OC | Skills as markdown files in `skills/` |
| OC's "main" session listening to Telegram | Nolty's tmux session with the Telegram plugin |
| OC's `action=send` channels | The `reply` MCP tool from `telegram@claude-plugins-official` |
| OC backend logging to PostgreSQL | Local files (`memory/`, `cron-runner/state/`); optional `examples/post-memory/` for external |
| `mcporter` tool calls | Native MCP tools in Claude Code (`mcp__claude_ai_*`, `mcp__perplexity__*`, etc.) |
| OC's memory store | `MEMORY.md` + `memory/YYYY-MM-DD.md` + (optionally) external activity feed |
| `oc` CLI | The `claude` CLI + slash commands + the `cron-management` skill |

## What's better in Nolty

- **No SDK credits.** OC ran in headless mode; Nolty is fully interactive Claude Code, staying on your standard plan after Anthropic's June 15 split.
- **Sub-agent dispatch.** OC ran crons in the main thread, blocking inbound chat. Nolty's main thread stays responsive while crons run as Task sub-agents.
- **Chrome MCP inheritance.** OC needed complex auth dance to get a browser session into a cron. Nolty's crons inherit Chrome from the main session.
- **First-class self-heal.** Heartbeat detects CC version drift and self-restarts. `/nolty-restart` recovers from hard crashes from any other Claude Code session.

## What's different / worse

- **No GUI cron table.** OC had a TUI; Nolty edits JSON or talks to `cron-management` in natural language.
- **No central activity feed.** OC's PostgreSQL logged everything; Nolty defaults to local logs. The `examples/post-memory/` skill shows how to plug in your own.
- **Single user.** OC supported multiple human users sharing one daemon; Nolty v1 is single-user.
- **macOS only (v1).** OC ran on Linux; Nolty's LaunchAgent is macOS-specific (Linux/Windows ports are post-v1 community work).

## Porting your existing OC setup

### Memory

Export your OC memory entries:

```bash
oc memory dump > /tmp/oc-memory.txt   # check `oc memory --help` for exact syntax
```

Curate to the 50-100 most important entries (not raw activity logs). Format as bullets, paste into `MEMORY.md`.

### Skills

Each OC skill is a procedure prompt. Convert to a slash command in `~/.claude/commands/<name>.md`:

```yaml
---
name: my-skill
description: One-line description
---

You are Nolty running my-skill.

If you see [cron model:X effort:Y] suffix, spawn a Task sub-agent.

## Procedure

[your procedure here]
```

For complex skills with internal helpers, use the `skills/<name>/SKILL.md` pattern (see `skills/cron-management/SKILL.md` for an example).

### Crons

Each OC cron entry maps to a JSON job in `cron-runner/cron-jobs.json`:

```json
{
  "id": "your-cron-id",
  "name": "Your Cron",
  "schedule": "30 6 * * *",
  "tz": "America/Chicago",
  "slash_command": "/your-skill",
  "model": "sonnet",
  "effort_level": "medium",
  "category": "info",
  "max_lag_minutes": 60,
  "enabled": true
}
```

Or just ask Nolty: "Add a cron that runs /your-skill daily at 6:30am, sonnet, medium." The `cron-management` skill will walk you through it.

### Tool calls

OC's `mcporter call X.Y` becomes a direct MCP tool name. Common mappings:

| OC | Nolty (Claude Code) |
|---|---|
| `mcporter call gmail.send` | `mcp__claude_ai_Gmail__*` or `gog gmail send` |
| `mcporter call calendar.list` | `mcp__claude_ai_Google_Calendar__list_events` or `gog calendar list` |
| `mcporter call zoom.summary` | `mcp__zapier__zoom_get_meeting_summary` |
| `mcporter call perplexity.search` | `mcp__perplexity__perplexity_search` |
| `mcporter call supabase.execute_sql` | `mcp__supabase__execute_sql` |
| `action=send, channel=telegram` | `reply` MCP tool (from `telegram@claude-plugins-official`) |

### Telegram

OC ran its own Telegram bot connection. In Nolty, the `telegram@claude-plugins-official` plugin handles it. See [SETUP_TELEGRAM.md](SETUP_TELEGRAM.md).

You can reuse your existing bot (and chat_id) — just put the token in the new location.

### Chrome / web-driven crons

OC needed `chrome-cli` or similar. Nolty uses `claude-in-chrome` MCP (built into CC). See [SETUP_CLAUDE_IN_CHROME.md](SETUP_CLAUDE_IN_CHROME.md).

### Personality / identity

OC's persona settings → `SOUL.md` + `IDENTITY.md` + `USER.md` files in Nolty. The shipped templates are a good starting point.

## Suggested migration order

1. **Week 1:** Set up Nolty in parallel with OC. Different Telegram bot, different chat_id (or new chat). Get the heartbeat working.
2. **Week 2:** Port one cron at a time — easiest first (a daily script-based cron is easier than a Chrome-driven one).
3. **Week 3:** Port memory + persona files. Test that Nolty behaves like your OC instance.
4. **Week 4:** Turn off OC daemon. Run only on Nolty.

Total time depends on how many crons you have. Brad's migration (15 crons) took ~5 days of evening work plus a couple of weeks of parallel-verify.

## After migration

- Keep your OC install around for 30 days as a safety net (just disable its daemon).
- After 30 days with no missed crons, fully uninstall OC.
- Save what you learned. If you want to contribute back, your migration notes might help the next person.
