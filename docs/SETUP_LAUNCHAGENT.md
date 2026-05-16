# Setup: LaunchAgent (cron-runner persistence)

The cron-runner is a Python script that wakes every 15 minutes via macOS launchd. This doc walks you through installing it so it persists across reboots.

## Critical: where the plist lives

macOS only auto-loads LaunchAgent plists from these directories at boot/login:

- `/Library/LaunchAgents/` (system-wide)
- `~/Library/LaunchAgents/` (per-user) ← we use this

**If your plist is anywhere else (like in the project directory only), macOS forgets about it after a reboot.** This caused a 27-hour outage during testing — don't skip the symlink step below.

## Step 1 — Customize the plist template

The template lives at `cron-runner/com.example.cron-runner.plist.template`. Copy it to your own label:

```bash
cd cron-runner

# Pick your reverse-DNS label. Examples:
#   com.yourname.cron-runner
#   net.yourcompany.cron-runner
#   org.yourdomain.cron-runner
LABEL="com.example.cron-runner"

cp com.example.cron-runner.plist.template "$LABEL.plist"
```

Edit `$LABEL.plist`:

1. Replace `com.example` with your label everywhere (search-and-replace).
2. Replace `/Users/YOUR_USER/` with your real home directory path.
3. Verify the Python path (the template uses `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3`). Run `which python3` and use that path if it differs.
4. Verify the `WorkingDirectory` and `ProgramArguments` paths point at your actual nolty checkout.

## Step 2 — Symlink into `~/Library/LaunchAgents/`

```bash
ln -sf "$(pwd)/$LABEL.plist" ~/Library/LaunchAgents/$LABEL.plist
```

Symlink (vs copy) means edits to the plist in the project directory flow through — single source of truth.

## Step 3 — Load the agent

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/$LABEL.plist
```

If this errors with "service already loaded", that's fine — unload first then re-load:

```bash
launchctl bootout gui/$(id -u)/$LABEL 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/$LABEL.plist
```

## Step 4 — Verify

```bash
# Should print the label with status 0
launchctl list | grep cron-runner

# Detailed status (state should be 'not running' between fires; that's normal)
launchctl print gui/$(id -u)/$LABEL | grep -E "state|last exit|run interval"
```

## Step 5 — Test fire

Force one immediate fire to verify Python + the runner work:

```bash
launchctl kickstart -k gui/$(id -u)/$LABEL
sleep 5
tail -10 cron-runner/logs/cron-runner.log
```

You should see a `run complete: dispatched=N skipped=M` line. If `dispatched=0` and you have enabled jobs, check timing — runner fires only jobs whose latest scheduled time is in their `max_lag_minutes` window.

## Step 6 — Unloading (for debugging)

If you need to stop the runner temporarily:

```bash
launchctl bootout gui/$(id -u)/$LABEL
```

To re-load:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/$LABEL.plist
```

## Step 7 — Uninstall (full removal)

```bash
launchctl bootout gui/$(id -u)/$LABEL
rm ~/Library/LaunchAgents/$LABEL.plist
```

The plist file in the project directory stays. Restart anytime by re-running the symlink + bootstrap.

## What if the Mac reboots?

After a reboot, macOS reads `~/Library/LaunchAgents/` at login and loads everything there. **The symlink in step 2 is what makes this work.** Without that symlink (just `launchctl bootstrap` from the project path), the agent doesn't survive a reboot.

To verify post-reboot:

```bash
# After login, before doing anything else:
launchctl list | grep cron-runner
# Should print your label. If empty, the symlink is missing or broken.
```

## Common issues

- **`launchctl: Could not find specified service`** — the agent isn't loaded. Run step 3 again.
- **`launchctl: Bootstrap failed: 5: Input/output error`** — the plist has a syntax error. Run `plutil -lint $LABEL.plist` to find it.
- **Agent loads but never fires** — check `logs/launchd.err.log`. Common causes: Python path wrong, croniter not installed for that Python version.
- **Fires but log says `skipped=N dispatched=0`** — your jobs are either disabled, or none are due in their lag window. Check `cron-runner.py list`.
