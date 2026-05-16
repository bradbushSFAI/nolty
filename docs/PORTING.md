# Porting Nolty to Linux or Windows

v0.1.0 supports macOS only. Linux is straightforward; Windows requires more work.

## macOS-isms in the current stack

| What's macOS-specific | Where it lives |
|---|---|
| `launchctl` + LaunchAgent plist | `cron-runner/com.example.cron-runner.plist.template`, install script |
| `~/Library/LaunchAgents/` boot persistence | `install.sh` |
| `pkill`, `pgrep`, `lsof`, `tmux` (Unix tools, also on Linux) | `clawd-restart.sh`, `/nolty-restart`, heartbeat STEP 0.5 |
| Bash scripts | `clawd-restart.sh`, `send-telegram.sh`, `install.sh`, `preflight-check.sh`, `scrub.sh` |
| Homebrew paths (`/opt/homebrew/bin/`) | hardcoded in skills |
| `~/.local/bin/claude` install path | `clawd-restart.sh` |

Everything else (Python, croniter, tmux, gog, Telegram plugin) is already cross-platform on POSIX.

## Linux port (~1 day)

The substitutions:

| macOS | Linux |
|---|---|
| LaunchAgent plist | systemd user unit: `~/.config/systemd/user/cron-runner.service` |
| `launchctl bootstrap gui/<uid>` | `systemctl --user enable cron-runner.service && systemctl --user start cron-runner.service` |
| `~/Library/LaunchAgents/` symlink | `systemctl --user enable` (handles persistence automatically) |
| `launchctl kickstart -k` | `systemctl --user restart cron-runner.service` |
| `launchctl list \| grep cron-runner` | `systemctl --user status cron-runner.service` |
| StartInterval = 900 in plist | `[Timer]` unit with `OnUnitActiveSec=15min` |
| `/opt/homebrew/bin/gog` | wherever `which gog` resolves (probably `/usr/local/bin/gog`) |
| `~/.local/share/claude/versions/` | same on Linux |
| `lsof` | same on Linux |

A `.service` + `.timer` pair gives you the same semantics as launchd's StartInterval:

```ini
# ~/.config/systemd/user/cron-runner.service
[Unit]
Description=Nolty cron-runner

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 %h/Documents/CodingProjects/nolty/cron-runner/bin/cron-runner.py run
WorkingDirectory=%h/Documents/CodingProjects/nolty/cron-runner

[Install]
WantedBy=default.target
```

```ini
# ~/.config/systemd/user/cron-runner.timer
[Unit]
Description=Run cron-runner every 15 minutes
Requires=cron-runner.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min

[Install]
WantedBy=timers.target
```

Enable:

```bash
systemctl --user daemon-reload
systemctl --user enable --now cron-runner.timer
```

Verify:

```bash
systemctl --user status cron-runner.timer
journalctl --user -u cron-runner.service --since "1 hour ago"
```

Update `clawd-restart.sh`, `/nolty-restart`, and `install.sh` to use systemd commands instead of `launchctl`. Update `heartbeat/SKILL.md`'s STEP 0.5 if your CC binary path differs (it shouldn't — `~/.local/share/claude/versions/` is the same).

**Estimated effort:** half a day for a contributor familiar with systemd user units.

## Windows port (significantly harder)

Two paths:

### Path A: WSL2 + Ubuntu inside (recommended)

1. Install WSL2 with Ubuntu
2. Install Python, tmux, croniter, gog, claude CLI inside WSL
3. Use systemd inside WSL2 (recent WSL versions support `systemctl --user`)
4. Telegram plugin works inside WSL — it's just HTTPS to api.telegram.org
5. **Catch:** `claude-in-chrome` lives in Windows-land Chrome, NOT inside WSL. So LinkedIn-style web crons either don't work or need a Windows-to-WSL bridge

If you don't run any Chrome-driven crons, WSL2 path is the easiest port. ~1 day, similar to the Linux port above.

### Path B: Native PowerShell (significant work, ~3-5 days)

- Rewrite `cron-runner.py` to use Windows Task Scheduler instead of LaunchAgent (still possible via `Register-ScheduledTask`)
- Replace `clawd-restart.sh`, `install.sh`, etc. with PowerShell equivalents
- Replace `tmux` with Windows Terminal + a persistent shell — but Windows Terminal doesn't have `send-keys` equivalent, so you'd need a different IPC mechanism (named pipes? socket?)
- Replace `pkill`/`pgrep`/`lsof` with PowerShell `Get-Process` / `Stop-Process`
- Possible but a major refactor

Most contributors will choose Path A.

## What you'd want to send upstream

If you port and want to contribute back:

1. Open an issue describing your platform + scope
2. PR keeps macOS as primary; adds platform detection in `install.sh` to branch on `uname`
3. New platform-specific scripts in `scripts/linux/` or `scripts/windows/`
4. A new doc `docs/PLATFORM_LINUX.md` (or `_WINDOWS.md`)
5. Update README to list supported platforms

The maintainer (Brad) will help review. Cross-platform support is welcome but not required for v1.
