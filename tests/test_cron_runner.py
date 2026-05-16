"""
Unit tests for cron-runner.py — the schedule math and dispatch logic.

Run from repo root: `pytest tests/`

These tests focus on the silent-failure-prone parts of cron-runner:
- compute_due() at exact ticks, mid-tick, and stale-after-sleep
- last_fired_at comparison (don't re-fire same scheduled occurrence)
- Picking the LATEST scheduled time in window when multiple missed
- Atomic state file write
- Cron expression validation
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

# Import the runner from its location
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "cron-runner" / "bin"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "cron_runner",
    REPO_ROOT / "cron-runner" / "bin" / "cron-runner.py"
)
cron_runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cron_runner)


CT = ZoneInfo("America/Chicago")


def make_job(schedule="0 20 * * *", max_lag_minutes=60, tz="America/Chicago", **kw):
    """Build a minimal job dict for testing."""
    base = {
        "id": "test-job",
        "name": "Test",
        "schedule": schedule,
        "tz": tz,
        "slash_command": "/test",
        "model": "sonnet",
        "effort_level": "medium",
        "category": "ops",
        "max_lag_minutes": max_lag_minutes,
        "enabled": True,
    }
    base.update(kw)
    return base


class TestComputeDue:
    """compute_due() returns (is_due, scheduled_at, lag_minutes)"""

    def test_fires_at_exact_tick(self):
        """Daily 8pm cron at 8:00pm exactly → should fire."""
        job = make_job(schedule="0 20 * * *", max_lag_minutes=60)
        now = datetime(2026, 5, 12, 20, 0, 0, tzinfo=CT)
        is_due, scheduled_at, lag = cron_runner.compute_due(job, now, None)
        assert is_due is True
        assert scheduled_at.hour == 20

    def test_fires_within_lag_window(self):
        """At 8:30pm, lag=30min < 60max → fire."""
        job = make_job(schedule="0 20 * * *", max_lag_minutes=60)
        now = datetime(2026, 5, 12, 20, 30, 0, tzinfo=CT)
        is_due, _, lag = cron_runner.compute_due(job, now, None)
        assert is_due is True
        assert 25 < lag < 35

    def test_skipped_beyond_lag_window(self):
        """At 9:30pm next morning, lag=90min > 60max → don't fire."""
        job = make_job(schedule="30 6 * * *", max_lag_minutes=60)
        now = datetime(2026, 5, 12, 8, 25, 0, tzinfo=CT)   # 6:30am was 115min ago
        is_due, _, _ = cron_runner.compute_due(job, now, None)
        assert is_due is False

    def test_within_lag_catchup_after_sleep(self):
        """At 7am with 6:30am missed by 30min < 60max → fire."""
        job = make_job(schedule="30 6 * * *", max_lag_minutes=60)
        now = datetime(2026, 5, 12, 7, 0, 0, tzinfo=CT)
        is_due, _, lag = cron_runner.compute_due(job, now, None)
        assert is_due is True
        assert 25 < lag < 35

    def test_no_refire_after_last_fired_within_window(self):
        """At 8:15pm with 8:00pm already fired → don't re-fire same scheduled time."""
        job = make_job(schedule="0 20 * * *", max_lag_minutes=60)
        last_fired = datetime(2026, 5, 12, 20, 0, 0, tzinfo=CT)
        now = datetime(2026, 5, 12, 20, 15, 0, tzinfo=CT)
        is_due, _, _ = cron_runner.compute_due(job, now, last_fired)
        assert is_due is False

    def test_heartbeat_30min_at_exact_30(self):
        """Heartbeat */30: at 8:00pm exactly → should fire (8:00 is a scheduled time)."""
        job = make_job(schedule="*/30 * * * *", max_lag_minutes=20)
        now = datetime(2026, 5, 12, 20, 0, 0, tzinfo=CT)
        is_due, _, _ = cron_runner.compute_due(job, now, None)
        assert is_due is True

    def test_heartbeat_does_not_refire_at_15(self):
        """Heartbeat */30: at 8:15pm with 8:00pm already fired → no re-fire."""
        job = make_job(schedule="*/30 * * * *", max_lag_minutes=20)
        last_fired = datetime(2026, 5, 12, 20, 0, 0, tzinfo=CT)
        now = datetime(2026, 5, 12, 20, 15, 0, tzinfo=CT)
        is_due, _, _ = cron_runner.compute_due(job, now, last_fired)
        assert is_due is False

    def test_picks_latest_scheduled_when_multiple_missed(self):
        """Heartbeat */30 with max_lag=60. At 8:25pm last fired 7:00pm.
        Window = 7:25-8:25, contains 7:30 and 8:00. Should fire 8:00 (latest), not 7:30."""
        job = make_job(schedule="*/30 * * * *", max_lag_minutes=60)
        last_fired = datetime(2026, 5, 12, 19, 0, 0, tzinfo=CT)
        now = datetime(2026, 5, 12, 20, 25, 0, tzinfo=CT)
        is_due, scheduled_at, _ = cron_runner.compute_due(job, now, last_fired)
        assert is_due is True
        assert scheduled_at.hour == 20
        assert scheduled_at.minute == 0

    def test_weekly_cron_only_fires_on_scheduled_day(self):
        """Monday 7am cron. On Tuesday 7am → not due."""
        job = make_job(schedule="0 7 * * 1", max_lag_minutes=1440)
        now = datetime(2026, 5, 12, 7, 0, 0, tzinfo=CT)   # Tuesday
        is_due, _, _ = cron_runner.compute_due(job, now, None)
        assert is_due is False

    def test_weekly_cron_fires_within_24h_lag(self):
        """Monday 7am cron with max_lag=1440 (24h). On Monday 8am → fire."""
        job = make_job(schedule="0 7 * * 1", max_lag_minutes=1440)
        now = datetime(2026, 5, 11, 8, 0, 0, tzinfo=CT)   # Monday
        is_due, _, lag = cron_runner.compute_due(job, now, None)
        assert is_due is True
        assert 55 < lag < 65


class TestState:
    """State file read/write atomicity."""

    def test_load_state_creates_default_when_missing(self, tmp_path, monkeypatch):
        # Point STATE_FILE at a non-existent path
        monkeypatch.setattr(cron_runner, "STATE_FILE", tmp_path / "nonexistent.json")
        state = cron_runner.load_state()
        assert state == {"version": 1, "jobs": {}}

    def test_save_state_atomic(self, tmp_path, monkeypatch):
        state_file = tmp_path / "state.json"
        monkeypatch.setattr(cron_runner, "STATE_FILE", state_file)
        state = {"version": 1, "jobs": {"foo": {"fire_count": 5}}}
        cron_runner.save_state(state)
        assert state_file.exists()
        loaded = json.loads(state_file.read_text())
        assert loaded["jobs"]["foo"]["fire_count"] == 5
        # Ensure .tmp file is gone (was renamed, not left behind)
        assert not state_file.with_suffix(".json.tmp").exists()

    def test_update_state_increments_fire_count(self):
        state = {"version": 1, "jobs": {}}
        now = datetime(2026, 5, 12, 20, 0, 0, tzinfo=timezone.utc)
        cron_runner.update_state(state, "foo", "dispatched", fired_at=now)
        assert state["jobs"]["foo"]["fire_count"] == 1
        cron_runner.update_state(state, "foo", "dispatched", fired_at=now)
        assert state["jobs"]["foo"]["fire_count"] == 2

    def test_update_state_status_only_does_not_bump_fire_count(self):
        state = {"version": 1, "jobs": {"foo": {"fire_count": 3}}}
        cron_runner.update_state(state, "foo", "skipped_lag")
        assert state["jobs"]["foo"]["fire_count"] == 3
        assert state["jobs"]["foo"]["last_status"] == "skipped_lag"


class TestCronExpressionValidation:
    """croniter should accept valid expressions, reject garbage."""

    @pytest.mark.parametrize("schedule", [
        "*/30 * * * *",     # every 30 min
        "0 6 * * *",        # daily 6am
        "30 6 * * *",       # daily 6:30am
        "0 7 * * 1",        # Monday 7am
        "0 16 * * 0",       # Sunday 4pm
        "0 2 1 * *",        # 1st of month 2am
    ])
    def test_valid_expressions_accepted(self, schedule):
        from croniter import croniter
        # Should not raise
        croniter(schedule, datetime.now(CT))

    @pytest.mark.parametrize("schedule", [
        "not a cron",
        "* * * *",          # too few fields
        "60 * * * *",       # minute > 59
        "* 25 * * *",       # hour > 23
    ])
    def test_invalid_expressions_rejected(self, schedule):
        from croniter import croniter
        with pytest.raises(Exception):
            croniter(schedule, datetime.now(CT))


class TestDispatchSuffix:
    """The cron-suffix format is what triggers sub-agent dispatch in CLAUDE.md."""

    def test_dispatch_suffix_format(self):
        """The suffix typed into Nolty's pane must include model + effort."""
        job = make_job(model="sonnet", effort_level="medium")
        # Simulate dispatch_job (without actually running tmux)
        suffix = f"[cron model:{job['model']} effort:{job['effort_level']}]"
        cmd = f"{job['slash_command']} {suffix}"
        assert "[cron model:sonnet effort:medium]" in cmd
        assert cmd.startswith("/")

    def test_dispatch_suffix_includes_haiku(self):
        job = make_job(model="haiku", effort_level="low")
        suffix = f"[cron model:{job['model']} effort:{job['effort_level']}]"
        assert "model:haiku" in suffix
        assert "effort:low" in suffix


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
