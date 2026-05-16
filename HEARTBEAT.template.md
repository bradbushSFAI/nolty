# HEARTBEAT.md — Proactive check-in protocol

> **Template:** copy to `HEARTBEAT.md` and customize timezone/hours. This file documents how Nolty's `/heartbeat` cron works.

## What heartbeat does

Every 30 minutes during your active hours, the `cron-runner` types `/heartbeat [cron model:sonnet effort:medium]` into Nolty's tmux pane. Nolty's main thread sees the `[cron ...]` suffix and spawns a Task sub-agent to run the check.

The sub-agent:

1. **STEP 0 — Time gate.** Reads current hour in your timezone. If outside active hours, exits with `QUIET_HOURS` and does NOTHING else. No tool calls, no Telegram, nothing.
2. **STEP 0.5 — Version-drift self-heal.** Compares the Claude Code version Nolty's tmux process is running against the latest version installed. If they differ (Claude Code auto-upgraded but tmux is stale), triggers a detached restart of Nolty's tmux session via `nohup ~/.claude/clawd-restart.sh &`. Then exits.
3. **STEP 1 — Identity refresh.** Briefly reads SOUL/IDENTITY/MEMORY to stay grounded.
4. **STEP 2 — Email scan.** Pulls unread email; flags only client replies, time-sensitive items.
5. **STEP 3 — Meeting check.** Pulls today's calendar; flags any meeting in the next 60 min not already reminded.
6. **STEP 4 — Alert.** If anything from steps 2-3 needs attention, sends ONE concise Telegram via `reply` with `chat_id`.
7. **STEP 5 — Silence.** If nothing urgent, replies `HEARTBEAT_OK <timestamp>` to the local tmux pane and exits. No Telegram for silent heartbeats.

## Configuration

In `USER.md`, set your active hours and timezone:

```
Timezone: America/Chicago
Active hours (CT): 7:00 AM – 11:00 PM
```

The `/heartbeat` skill (`skills/heartbeat/SKILL.md`) reads these and gates accordingly.

## Why every 30 min?

Frequent enough to catch a new urgent email within half an hour. Infrequent enough to not drain credit / context. Configurable in `cron-runner/cron-jobs.json` — set `schedule: "*/30 * * * *"` for 30-min, `*/15` for 15-min, etc.

## Dedup rule

Meeting reminders are deduplicated via `memory/heartbeat-state.json` → `remindedEvents` array. Once an event is alerted, it won't ping again that day. This prevents the same 10am meeting from being pinged at 9:00, 9:30, 9:30 (next heartbeat), etc.

## Hard rules (also in SOUL.md)

1. **Quiet hours are absolute.** Outside active hours → no tool calls, no Telegram, just `QUIET_HOURS` and exit.
2. **Never send a silent "nothing to report" Telegram.** Silence = `HEARTBEAT_OK` in the pane only.
3. **Use `reply` MCP tool**, not `send-telegram.sh`.

---

Customize timezone and hours per your needs. The rest is the canonical protocol.
