---
name: nolty-restart
description: Diagnose and recover the Nolty stack from a hard crash. Use when Telegram has gone silent, no crons have fired, or you suspect the whole system is wedged. Runs from any Claude Code session (doesn't depend on Nolty being alive).
---

You are the recovery agent for the Nolty stack.

When something is broken across the whole system — Telegram silent for hours, no recent cron fires, Nolty unresponsive — the user invokes this slash command from any Claude Code session (terminal, VS Code, even a different folder). Your job: diagnose every layer, fix what's broken, and report the result.

Set `NOLTY_HOME` to the path of your nolty/ checkout if not at the default. Default: `~/Documents/CodingProjects/nolty`.

## Components to check

| Component | Healthy state |
|---|---|
| tmux session `CC_running_like_OC` | exists |
| `claude --channels plugin:telegram@...` process | alive, child of the tmux pane |
| Running claude binary version | matches latest in `~/.local/share/claude/versions/` |
| `bun run ... external_plugins/telegram` process | alive |
| Cron-runner LaunchAgent | loaded in `launchctl list` |
| Persistence symlink in `~/Library/LaunchAgents/` | exists |
| `cron-runner/state/cron-state.json` `last_check_at` | within the last ~16 minutes (runner fires every 15) |

## Procedure

### Step 1 — Diagnose

Run these checks in order. Record findings. Do NOT fix anything yet.

```bash
NOLTY_HOME="${NOLTY_HOME:-$HOME/Documents/CodingProjects/nolty}"

echo "=== time ==="
date
echo ""
echo "=== tmux session ==="
tmux has-session -t CC_running_like_OC 2>&1 && echo "  ✓ tmux alive" || echo "  ✗ tmux MISSING"
echo ""
echo "=== claude + bun processes ==="
ps aux | grep -E '\.local/bin/claude.*--channels|bun.*telegram' | grep -v grep
echo ""
echo "=== claude version state ==="
echo "  installed versions:" && ls -1 ~/.local/share/claude/versions/ 2>/dev/null
PANE_PID=$(tmux list-panes -t CC_running_like_OC -F '#{pane_pid}' 2>/dev/null | head -1)
CLAUDE_PID=$(pgrep -P "$PANE_PID" -f 'claude.*--channels' 2>/dev/null | head -1)
RUNNING=$(lsof -p "$CLAUDE_PID" 2>/dev/null | grep -oE 'versions/[0-9]+\.[0-9]+\.[0-9]+' | head -1 | cut -d/ -f2)
LATEST=$(ls -1 ~/.local/share/claude/versions/ 2>/dev/null | sort -V | tail -1)
echo "  running=$RUNNING latest=$LATEST"
echo ""
echo "=== cron-runner LaunchAgent ==="
launchctl list 2>&1 | grep cron-runner || echo "  ✗ NOT LOADED"
echo ""
echo "=== persistence symlink ==="
ls -la ~/Library/LaunchAgents/ 2>/dev/null | grep cron-runner || echo "  ✗ no plist in ~/Library/LaunchAgents/"
echo ""
echo "=== cron-runner state freshness ==="
python3 -c "
import json, time
from datetime import datetime, timezone
try:
    d = json.load(open('$NOLTY_HOME/cron-runner/state/cron-state.json'))
    last = max((j['last_check_at'] for j in d['jobs'].values() if 'last_check_at' in j), default=None)
    if last:
        delta_s = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds()
        print(f'  most recent check: {last} ({delta_s/60:.1f} min ago)')
        print(f'  STALE' if delta_s > 1200 else f'  FRESH')
    else:
        print('  no state recorded')
except Exception as e:
    print(f'  ERROR reading state: {e}')
"
```

### Step 2 — Classify

Based on findings, pick the smallest recovery path that fixes the actual failure. Do not blast-restart everything if only one thing is broken.

| Symptom | Fix |
|---|---|
| tmux MISSING | `$NOLTY_HOME/clawd-restart.sh` |
| tmux alive but no `claude --channels` process child | `$NOLTY_HOME/clawd-restart.sh` |
| Running version != Latest (drift) | `$NOLTY_HOME/clawd-restart.sh` |
| bun telegram process missing but claude alive | `$NOLTY_HOME/clawd-restart.sh` (fresh bun) |
| cron-runner NOT LOADED in launchctl | `launchctl bootstrap gui/$(id -u) <plist path>` |
| Persistence symlink missing in `~/Library/LaunchAgents/` | `ln -sf <plist> ~/Library/LaunchAgents/...` |
| Cron-runner state STALE (>16 min) but loaded | `launchctl kickstart -k gui/$(id -u)/com.<your-rdns>.cron-runner` |
| Everything green | nothing — exit with green report |

### Step 3 — Apply fixes

**Restart Nolty's tmux session:**
```bash
"$NOLTY_HOME/clawd-restart.sh" 2>&1 | tail -5
sleep 12  # boot time
```

**Bootstrap cron-runner LaunchAgent:**
```bash
# Find the user's plist (matches *cron-runner*)
PLIST=$(ls ~/Library/LaunchAgents/*cron-runner*.plist 2>/dev/null | head -1)
[ -n "$PLIST" ] && launchctl bootstrap gui/$(id -u) "$PLIST" 2>&1
launchctl list | grep cron-runner
```

**Add persistence symlink (if missing):**
```bash
ln -sf "$NOLTY_HOME/cron-runner/com.<your-rdns>.cron-runner.plist" \
       ~/Library/LaunchAgents/com.<your-rdns>.cron-runner.plist
```

**Force one cron-runner wake (catches up stale schedules within max_lag windows):**
```bash
launchctl kickstart -k gui/$(id -u)/com.<your-rdns>.cron-runner
```

### Step 4 — Verify

After fixes, re-run the same checks from Step 1. Confirm every layer is green. If anything is still broken, name what and why.

### Step 5 — Report

Output a concise summary:

```
🛠 nolty-restart — <date/time>

Findings:
- <one line per check, ✓ or ✗>

Fixes applied:
- <one line per action>

Result: <RECOVERED | PARTIAL | STILL BROKEN>
<if PARTIAL or STILL BROKEN, explain what's left>
```

## Notes

- This skill is for **hard-crash recovery**, not health drift. The heartbeat skill (`STEP 0.5`) handles routine version-drift auto-restart during waking hours.
- If you can't reach tmux at all (the binary isn't installed, fresh machine), report that — don't try to install tmux yourself.
- Don't touch unrelated LaunchAgents.
