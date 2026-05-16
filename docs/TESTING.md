# Testing

Two layers: mechanical tests (pytest + preflight script, ship in repo) and integration tests (fresh-user simulation, run before tagging a release).

## Mechanical tests

### pytest

Run from repo root:

```bash
pytest tests/
```

Covers `cron-runner.py`'s schedule math — the silent-failure-prone part:

- `compute_due()` at exact-tick, mid-tick, and stale-after-sleep
- Multiple missed scheduled fires → picks LATEST within window
- `last_fired_at` comparison: don't re-fire the same scheduled occurrence
- Cron expression validation rejects garbage
- Atomic state file write (no partial JSON on crash)

If pytest exits 0, the scheduling logic is sound.

### preflight-check.sh

Run after install to verify your environment:

```bash
./scripts/preflight-check.sh
```

Checks:

- Python ≥ 3.9 on PATH
- `croniter` importable
- tmux on PATH
- `claude` CLI on PATH
- LaunchAgent plist exists in `~/Library/LaunchAgents/`
- LaunchAgent loaded in `launchctl list`
- `cron-jobs.json` parses
- `state/` and `logs/` directories writable
- Telegram bot token + chat_id readable in `~/.claude/channels/telegram/.env`

Each check prints `✓` or `✗` with a one-line fix hint. Exit non-zero if any `✗`.

## Fresh-user simulation

The recommended gating test before tagging a release. Catches install-script bugs, hardcoded paths, missing dependencies.

### Procedure

1. **Create a test macOS user account.** System Settings → Users & Groups → add `test-nolty` user.
2. **Log into that account** (logout + log back in as test-nolty, or `su - test-nolty`).
3. **Clone the public repo** into the test user's home:

   ```bash
   git clone https://github.com/bradbushSFAI/nolty.git ~/Documents/CodingProjects/nolty
   cd ~/Documents/CodingProjects/nolty
   ```

4. **Follow the public README verbatim.** Install Python + tmux + croniter. Set up a Telegram bot (a NEW one for this test — don't reuse your real one). Copy templates. Run `./scripts/install.sh`.
5. **Verify end-to-end:**

   - `./scripts/preflight-check.sh` → all `✓`
   - `./clawd-restart.sh` → tmux session boots, claude starts
   - Send the test bot a message → get a reply within 30 seconds
   - Wait 15-30 min → heartbeat fires (check `cron-runner/logs/cron-runner.log`)

6. **Delete the test user** when done. System Settings → Users → remove `test-nolty` + their home folder.

Cost: 1-2 hours of focused time per release. Catches the "works on my Mac" class of bug that no unit test would.

## Beta tester

Before going wide (any release tagged beyond v0.1.0), recruit ONE real OpenClaw user to follow the public README from their own Mac. Be available on Slack/Discord/email to debug what they hit live.

This catches:
- Documentation gaps
- Assumed knowledge ("did the user know to install tmux?")
- Undocumented macOS state assumptions
- Real-world Telegram bot setup confusion
- Things you can't see because you wrote the docs

Most valuable single piece of feedback before a wide release.

## What testing won't catch

- **Long-running drift.** The boot-persistence bug took 2 days to surface during testing. Some failures only happen after rebooting.
- **Telegram bot API changes.** Out of your control.
- **Claude Code version upgrades that change inheritance behavior.** Hard to test in advance.
- **Bot-detection on third-party sites.** LinkedIn etc. may change behavior at any time.

For these, the toolkit relies on `/nolty-restart` and heartbeat self-heal — recovery, not prevention.

## What to test when adding a new skill

1. **Unit-test schedule changes** if you've added to `cron-runner/cron-jobs.json` with unusual schedule expressions. `pytest tests/test_cron_runner.py -k <expression>` should pass.
2. **Force-fire once before enabling.** `python3 cron-runner/bin/cron-runner.py fire <new-job-id>` while `enabled: false`. Verify the slash command appears in Nolty's pane and the work runs cleanly.
3. **Watch the first real fire.** `tmux attach -t CC_running_like_OC` at the scheduled time. Even if you've force-fired before, the real fire path (via launchd → cron-runner → tmux) is the test that matters.

## CI

There's no CI configured in v0.1.0. If you want to add one:

- pytest is enough for the runner logic
- The fresh-user sim and Telegram tests can't run in CI — they need a real Mac and a real Telegram bot
- A GitHub Actions config for pytest would catch the most obvious regressions
