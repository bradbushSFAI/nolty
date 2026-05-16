# Recovery

When something feels wrong with Nolty — Telegram silent, no recent cron fires, weird behavior — run `/nolty-restart` from any Claude Code session. This doc explains what it does and when manual recovery is needed.

## The `/nolty-restart` slash command

`/nolty-restart` is installed at `~/.claude/commands/nolty-restart.md`. It works from ANY Claude Code session — terminal, an IDE, a different project. It does NOT require Nolty herself to be alive.

### Invoke

In any Claude Code session:

```
/nolty-restart
```

### What it does

1. **Diagnoses** every layer:
   - tmux session exists?
   - claude process child of the tmux pane alive?
   - bun (Telegram plugin) process alive?
   - claude binary version matches latest installed?
   - cron-runner LaunchAgent loaded?
   - Persistence symlink in `~/Library/LaunchAgents/`?
   - `cron-state.json` `last_check_at` within last ~16 min?

2. **Classifies** the failure based on findings.

3. **Applies the smallest fix** that restores function:
   - tmux/process/version issues → `clawd-restart.sh`
   - LaunchAgent unloaded → `launchctl bootstrap`
   - Symlink missing → `ln -sf` it
   - LaunchAgent stale → `launchctl kickstart`
   - Everything green → reports no action needed

4. **Re-verifies** and reports `RECOVERED`, `PARTIAL`, or `STILL BROKEN`.

### Reading the report

The skill outputs a structured summary:

```
🛠 nolty-restart — 2026-05-16 11:49

Findings:
- ✓ tmux session alive
- ✓ claude process alive (PID 32584)
- ✗ Running version 2.1.140 != Latest 2.1.143
- ✓ cron-runner loaded
- ✓ symlink present
- ✓ state fresh (3.2 min ago)

Fixes applied:
- Restarted Nolty's tmux session (clawd-restart.sh)
- Re-verified: running version now 2.1.143

Result: RECOVERED
```

## Common scenarios

### "Telegram has been silent for hours"

Most often: Claude Code auto-upgraded and Nolty's tmux process is stale. `/nolty-restart` will detect the version drift and respawn the tmux session. Within a minute you should be able to message your bot again.

(The heartbeat skill normally catches this within 30 min via STEP 0.5 — but if you noticed first, `/nolty-restart` is the immediate fix.)

### "No crons have fired since yesterday morning"

Most often: Mac rebooted and the cron-runner LaunchAgent isn't in `~/Library/LaunchAgents/` (only in the project directory). `/nolty-restart` will detect the missing symlink, create it, bootstrap the agent, and force one fire to catch up.

### "Nolty replies to me but doesn't seem to know who I am"

The session loaded successfully but the foundation files (SOUL/IDENTITY/USER/MEMORY) aren't being read. Check:

- Do all the `*.md` files exist? (`ls *.md` in the nolty root)
- Is the `CLAUDE.md` loading them via the "On session start" instructions?
- Does the new tmux session have the right cwd? (Should be `TelegramConfig/`, not the parent.)

If those look fine and behavior is still weird, restart Nolty: `./clawd-restart.sh`.

### "I see a slash command in the pane but nothing happens"

The slash command was typed into Nolty's input box but never submitted (no Enter). Or Nolty is busy with something else.

Press Enter on the pane (`tmux attach -t CC_running_like_OC`, then Enter), or wait for her current task to finish.

If she's been stuck for >10 min, restart: `./clawd-restart.sh`.

## Manual recovery (when `/nolty-restart` itself can't run)

If `/nolty-restart` doesn't work — like if Claude Code itself is broken on your machine — do these checks manually in any terminal:

```bash
# 1. Is tmux running?
tmux has-session -t CC_running_like_OC && echo "✓" || echo "✗ missing"

# 2. Is claude running inside it?
ps aux | grep -E '\.local/bin/claude.*--channels' | grep -v grep

# 3. Is the cron-runner loaded?
launchctl list | grep cron-runner

# 4. Is the plist symlinked?
ls -la ~/Library/LaunchAgents/ | grep cron-runner
```

Then apply fixes:

```bash
NOLTY_HOME=~/Documents/CodingProjects/nolty

# Restart Nolty
$NOLTY_HOME/clawd-restart.sh

# Reload cron-runner
LABEL="com.yourname.cron-runner"   # whatever your label is
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/$LABEL.plist 2>/dev/null

# Add symlink if missing
ln -sf "$NOLTY_HOME/cron-runner/$LABEL.plist" \
       ~/Library/LaunchAgents/$LABEL.plist

# Force a fire
launchctl kickstart -k gui/$(id -u)/$LABEL
```

## When to suspect bigger issues

- **All checks ✓ but Telegram still silent** — the bot token might be revoked or the bot might be blocked by Telegram. Try `/sendMessage` via curl directly:

  ```bash
  curl "https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=test"
  ```

  If that returns `"ok":true`, the token + bot are fine — the issue is between the plugin and Telegram. If it errors, regenerate the token via BotFather.

- **CC auto-upgrade keeps breaking things** — file an issue with Anthropic. The heartbeat self-heal should mitigate, but persistent breakage means CC's binary swap protocol changed.

- **LaunchAgent loads but never fires** — Python or croniter is broken. Check `cron-runner/logs/launchd.err.log`.
