#!/usr/bin/env python3
"""
cron-runner.py — Nolty's self-hosted cron dispatcher.

Replaces runCLAUDErun. Wakes every 15 min via LaunchAgent, checks cron-jobs.json
for jobs due since their last fire, and dispatches each one into Nolty's tmux
session as a slash command. Nolty's CLAUDE.md routing rule spawns a Task
sub-agent for each, so her main thread stays free for Brad's chat.

Failure mode: if Nolty's tmux session is missing, jobs are skipped and an alert
is sent via send-telegram.sh. State for each job is tracked in
state/cron-state.json (last_fired_at, status, fire_count).
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    from croniter import croniter
except ImportError:
    print("ERROR: croniter not installed. Run: pip3.14 install croniter", file=sys.stderr)
    sys.exit(2)


ROOT = Path(__file__).resolve().parent.parent
JOBS_FILE = ROOT / "cron-jobs.json"
STATE_FILE = ROOT / "state" / "cron-state.json"
LOG_FILE = ROOT / "logs" / "cron-runner.log"
SEND_TELEGRAM = ROOT / "bin" / "send-telegram.sh"
TMUX_SESSION = "CC_running_like_OC"
TMUX_BIN = "/opt/homebrew/bin/tmux"


def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_jobs():
    with open(JOBS_FILE) as f:
        return json.load(f)


def load_state():
    if not STATE_FILE.exists():
        return {"version": 1, "jobs": {}}
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    tmp.replace(STATE_FILE)


def tmux_has_session():
    result = subprocess.run(
        [TMUX_BIN, "has-session", "-t", TMUX_SESSION],
        capture_output=True,
    )
    return result.returncode == 0


def tmux_send(text):
    subprocess.run(
        [TMUX_BIN, "send-keys", "-t", TMUX_SESSION, text, "Enter"],
        check=True,
    )


def send_telegram_alert(msg):
    try:
        subprocess.run([str(SEND_TELEGRAM), msg], check=False, timeout=15)
    except Exception as e:
        logging.error(f"send-telegram failed: {e}")


def parse_iso(s):
    if not s:
        return None
    return datetime.fromisoformat(s)


def compute_due(job, now, last_fired_at):
    """
    Return (is_due, scheduled_at, lag_minutes).

    A job is due if there is a scheduled fire in the window
    (now - max_lag, now] that hasn't already been fired (i.e. is strictly
    after last_fired_at). We pick the latest such scheduled fire so we
    skip stale catch-up fires when multiple have been missed.
    """
    tz = ZoneInfo(job.get("tz", "America/Chicago"))
    now_tz = now.astimezone(tz)
    max_lag = job.get("max_lag_minutes", 60)
    window_start = now_tz - timedelta(minutes=max_lag)

    cron = croniter(job["schedule"], window_start)
    latest_in_window = None
    while True:
        nxt = cron.get_next(datetime)
        if nxt > now_tz:
            break
        latest_in_window = nxt

    if latest_in_window is None:
        return False, None, None

    if last_fired_at:
        last_tz = last_fired_at.astimezone(tz) if last_fired_at.tzinfo else last_fired_at.replace(tzinfo=tz)
        if latest_in_window <= last_tz:
            return False, latest_in_window, None

    lag_minutes = (now_tz - latest_in_window).total_seconds() / 60.0
    return True, latest_in_window, lag_minutes


def dispatch_job(job, scheduled_at, dry_run=False):
    suffix = f"[cron model:{job['model']} effort:{job['effort_level']}]"
    cmd = f"{job['slash_command']} {suffix}"
    logging.info(f"DISPATCH {job['id']} -> {cmd}")
    if dry_run:
        return "dry_run"
    if not tmux_has_session():
        msg = f"⚠️ Nolty tmux session down; skipped cron {job['id']}"
        logging.warning(msg)
        send_telegram_alert(msg)
        return "skipped_nolty_down"
    try:
        tmux_send(cmd)
        return "dispatched"
    except subprocess.CalledProcessError as e:
        logging.error(f"tmux send-keys failed for {job['id']}: {e}")
        return "tmux_send_failed"


def update_state(state, job_id, status, fired_at=None):
    entry = state["jobs"].get(job_id, {"fire_count": 0})
    if status == "dispatched":
        entry["last_fired_at"] = fired_at.isoformat()
        entry["fire_count"] = entry.get("fire_count", 0) + 1
    entry["last_status"] = status
    entry["last_check_at"] = datetime.now(timezone.utc).isoformat()
    state["jobs"][job_id] = entry


def cmd_run(args):
    jobs_doc = load_jobs()
    state = load_state()
    now = datetime.now(timezone.utc)
    if args.now:
        now = datetime.fromisoformat(args.now)
        if now.tzinfo is None:
            now = now.replace(tzinfo=ZoneInfo("America/Chicago"))

    dispatched = 0
    skipped = 0
    for job in jobs_doc["jobs"]:
        if not job.get("enabled", False) and not args.force:
            continue
        if args.only and job["id"] != args.only:
            continue
        last_fired = parse_iso(state["jobs"].get(job["id"], {}).get("last_fired_at"))
        is_due, scheduled_at, lag = compute_due(job, now, last_fired)
        if not is_due:
            if lag is not None and lag > job.get("max_lag_minutes", 60):
                logging.info(f"SKIP {job['id']}: lag {lag:.1f}m > max {job['max_lag_minutes']}m")
                update_state(state, job["id"], "skipped_lag")
                skipped += 1
            continue
        status = dispatch_job(job, scheduled_at, dry_run=args.dry_run)
        if status in ("dispatched", "dry_run"):
            update_state(state, job["id"], "dispatched" if status == "dispatched" else "dry_run", fired_at=now)
            dispatched += 1
        else:
            update_state(state, job["id"], status)
            skipped += 1

    if not args.dry_run:
        save_state(state)
    logging.info(f"run complete: dispatched={dispatched} skipped={skipped}")
    return 0


def cmd_force_run(args):
    """Bypass schedule check; fire a single job immediately."""
    jobs_doc = load_jobs()
    state = load_state()
    job = next((j for j in jobs_doc["jobs"] if j["id"] == args.id), None)
    if not job:
        print(f"ERROR: no job with id={args.id}", file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc)
    status = dispatch_job(job, now, dry_run=args.dry_run)
    if status == "dispatched":
        update_state(state, job["id"], "dispatched", fired_at=now)
        save_state(state)
    print(f"{job['id']}: {status}")
    return 0


def cmd_list(args):
    jobs_doc = load_jobs()
    state = load_state()
    now = datetime.now(ZoneInfo("America/Chicago"))
    rows = []
    for job in jobs_doc["jobs"]:
        st = state["jobs"].get(job["id"], {})
        cron = croniter(job["schedule"], now)
        next_fire = cron.get_next(datetime).strftime("%Y-%m-%d %H:%M %Z")
        last = st.get("last_fired_at", "—")
        status = st.get("last_status", "—")
        rows.append({
            "id": job["id"],
            "enabled": job["enabled"],
            "schedule": job["schedule"],
            "model": job["model"],
            "effort": job["effort_level"],
            "next": next_fire,
            "last": last,
            "status": status,
        })
    print(json.dumps(rows, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=False)

    p_run = sub.add_parser("run", help="Check schedules and dispatch due jobs")
    p_run.add_argument("--dry-run", action="store_true")
    p_run.add_argument("--now", help="Override current time (ISO format, for testing)")
    p_run.add_argument("--only", help="Limit to a single job id")
    p_run.add_argument("--force", action="store_true", help="Include disabled jobs in scheduling check")
    p_run.set_defaults(func=cmd_run)

    p_force = sub.add_parser("fire", help="Force-fire a single job immediately")
    p_force.add_argument("id")
    p_force.add_argument("--dry-run", action="store_true")
    p_force.set_defaults(func=cmd_force_run)

    p_list = sub.add_parser("list", help="Print all jobs as JSON with next/last fire info")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    if not args.cmd:
        args.cmd = "run"
        args.dry_run = False
        args.now = None
        args.only = None
        args.force = False
        args.func = cmd_run

    setup_logging()
    try:
        return args.func(args)
    except Exception as e:
        logging.exception(f"cron-runner crashed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
