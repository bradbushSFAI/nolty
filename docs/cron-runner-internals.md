# cron-runner internals

## `cron-jobs.json` schema

```json
{
  "version": 1,
  "description": "free-form note",
  "tz_default": "America/Chicago",
  "jobs": [
    {
      "id": "kebab-case-unique-id",
      "name": "Human label",
      "description": "What this cron does",
      "schedule": "*/30 * * * *",
      "tz": "America/Chicago",
      "slash_command": "/heartbeat",
      "model": "sonnet",
      "effort_level": "medium",
      "category": "ops",
      "max_lag_minutes": 20,
      "enabled": true,
      "created_at": "2026-05-16T00:00:00-05:00",
      "notes": ""
    }
  ]
}
```

### Field reference

| Field | Type | Notes |
|---|---|---|
| `id` | string | kebab-case, unique. Used as the key in `cron-state.json`. |
| `name` | string | Human-readable label. Shown in `cron-management` list. |
| `description` | string | Used by the agent to understand what the cron does. |
| `schedule` | string | Standard cron expression. Validated with `croniter`. |
| `tz` | string | IANA timezone (e.g. `America/Chicago`). Defaults to top-level `tz_default`. |
| `slash_command` | string | The slash command to dispatch. Must start with `/`. |
| `model` | `haiku` \| `sonnet` \| `opus` | Sent in the cron-suffix `[cron model:X ...]` for sub-agent dispatch. |
| `effort_level` | `low` \| `medium` \| `high` | Sent in the cron-suffix. |
| `category` | `info` \| `marketing` \| `ops` \| `sales` | Free-form labeling for filtering. |
| `max_lag_minutes` | integer | If the most recent scheduled fire was more than this many minutes ago, skip rather than late-fire. Suggested defaults: heartbeat=20, daily=60, weekly=1440, monthly=2880. |
| `enabled` | bool | If false, the runner skips this job entirely. |
| `created_at` | ISO 8601 string | Informational. |
| `notes` | string | Free-form. |

## `cron-state.json` schema

```json
{
  "version": 1,
  "jobs": {
    "heartbeat": {
      "last_fired_at": "2026-05-15T13:08:07.737240+00:00",
      "last_status": "dispatched",
      "last_check_at": "2026-05-15T13:08:07.757259+00:00",
      "fire_count": 94
    }
  }
}
```

Fields:

- `last_fired_at` — UTC timestamp of the most recent successful dispatch
- `last_status` — one of `dispatched`, `dry_run`, `skipped_lag`, `skipped_nolty_down`, `tmux_send_failed`
- `last_check_at` — UTC timestamp of the most recent runner wake (whether or not the job fired)
- `fire_count` — total successful dispatches since file was created

The runner writes this file atomically (write to `.tmp`, rename) so a kill mid-write can't corrupt it. The file is gitignored.

## Scheduling logic

The runner wakes every 15 minutes via the LaunchAgent's `StartInterval`. On each wake, for each enabled job:

```
window_start = now - max_lag_minutes
cron = croniter(schedule, window_start)
latest_in_window = None
loop:
    nxt = cron.get_next()
    if nxt > now: break
    latest_in_window = nxt

if latest_in_window is None:
    skip (no scheduled fire in window)

if last_fired_at and latest_in_window <= last_fired_at:
    skip (already fired this scheduled occurrence)

dispatch(job)
```

The window approach correctly handles:

- **Exact-tick fires** — if a job is scheduled for 8:00pm and now is 8:00pm exactly, `latest_in_window == 8:00pm` and it fires.
- **Mid-tick** — if now is 8:15pm and the last fire was the 8:00pm scheduled one, the 8:15 check skips (no new scheduled fire since).
- **Stale-after-sleep** — if the Mac was asleep and now is 8:25am while the last scheduled fire was 6:30am, `lag = 115min > max_lag=60` → skip (don't fire a stale brief mid-morning).
- **Within-lag catch-up** — if now is 7:00am and the 6:30am fire was missed by 30m < max_lag=60, fire.
- **Multiple missed fires** — the loop walks ALL scheduled times in window and picks the LATEST. So if you missed three heartbeats, you only fire ONE (the most recent one), not three.

## Dispatch action

```python
suffix = f"[cron model:{job['model']} effort:{job['effort_level']}]"
cmd = f"{job['slash_command']} {suffix}"
tmux send-keys -t CC_running_like_OC "$cmd" Enter
```

That's it. The runner doesn't wait for the sub-agent to finish — it just types and moves on to the next job. State updates synchronously after each successful `send-keys`.

If `tmux has-session` returns non-zero (Nolty's session is dead), the runner skips the dispatch and sends an emergency Telegram via `bin/send-telegram.sh` so the user knows.

## CLI

```bash
# Normal mode (called by launchd every 15 min)
python3 cron-runner/bin/cron-runner.py run

# Dry-run: print what would fire without actually dispatching
python3 cron-runner/bin/cron-runner.py run --dry-run

# Force-fire a specific job immediately (bypass schedule check)
python3 cron-runner/bin/cron-runner.py fire <job-id>

# List all jobs as JSON with computed next-fire times
python3 cron-runner/bin/cron-runner.py list

# Force schedule check at a specific time (for testing)
python3 cron-runner/bin/cron-runner.py run --dry-run --now '2026-05-12T20:00:00-05:00'

# Force check disabled jobs too (for testing)
python3 cron-runner/bin/cron-runner.py run --dry-run --force --only audible-deals
```

See `tests/test_cron_runner.py` for the canonical examples of each.

## Logging

`logs/cron-runner.log` — one line per wake, plus DISPATCH lines for each fired job. Rotation: none (the file grows; rotate manually if it gets big).

`logs/launchd.out.log` and `logs/launchd.err.log` — stdout/stderr from the launchd-spawned Python process. err.log should be empty in healthy operation.

## Failure modes summary

| Failure | How runner responds |
|---|---|
| Job's `enabled: false` | Silently skipped |
| Lag > max_lag | `last_status = skipped_lag` |
| `tmux has-session` fails | `last_status = skipped_nolty_down`, send emergency Telegram |
| `tmux send-keys` fails | `last_status = tmux_send_failed` |
| Python crash | launchd records non-zero exit in `launchd.err.log`, restarts on next interval |
