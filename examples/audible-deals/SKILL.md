---
name: audible-deals
description: Daily 8pm Audible deals digest — runs a scan script, emails matches to a chosen recipient. EXAMPLE — adapt to your own setup.
---

# Audible Deals (example)

> **EXAMPLE — adapt to your own setup.** Demonstrates the script-driven cron pattern: run a Python script, format output, email to a third party. Uses [`audible-deals`](https://github.com/chauduyphanvu/audible-deals) (public CLI).

You are Nolty running the nightly Audible deals scan.

If you see `[cron model:X effort:Y]` suffix, spawn a Haiku sub-agent.

## Setup

Install the audible-deals CLI:

```bash
pip install audible-deals
deals --help    # should print usage
```

Configure your scan profiles (taste filters) — see audible-deals docs. The skill below assumes profiles named `your-genre-1`, `your-genre-2`, etc.

## Procedure

### STEP 1 — Run the scan script

```bash
/usr/bin/python3 examples/audible-deals/scripts/scan_deals.py --output /tmp/audible-digest.md
```

(Adapt the script path to your install location. The script wraps the `deals` CLI calls across your profiles.)

The scan can take several minutes — multiple Audible API calls. If the script exits non-zero or the digest file is empty, skip the email and notify the user (STEP 4).

### STEP 2 — Email the digest

Use absolute path — sub-agent shells don't always have `/opt/homebrew/bin` on PATH:

```bash
/opt/homebrew/bin/gog gmail send \
  --to ${RECIPIENT_EMAIL} \
  --subject "📚 Audible Deals — $(date +'%b %d')" \
  --body-file /tmp/audible-digest.md \
  --account YOUR_EMAIL@example.com
```

Success looks like two TSV lines: `message_id\t<id>` and `thread_id\t<id>`. If non-zero exit OR no `message_id` in output, the send failed — STEP 4 failure path.

**Do NOT fall back to `gog gmail create_draft`.** Drafts don't reach the recipient. Silent fallback is exactly the failure mode this skill is designed to avoid.

### STEP 3 — Log to memory

Append to `memory/YYYY-MM-DD.md`: `20:00 — Audible deals digest sent to ${RECIPIENT_EMAIL}. message_id=<id>`

### STEP 4 — On success / failure

- **Success (message_id confirmed):** finish silently with `AUDIBLE_OK <timestamp>`. No Telegram. The email IS the deliverable.
- **Any failure** (script non-zero, empty digest, no message_id, anything unexpected): call `reply` MCP tool with a short message (<200 chars) — e.g. "⚠️ Audible deals failed: gog send returned no message_id. Digest at /tmp/audible-digest.md (4.6kb). Recipient did NOT get it." End with `AUDIBLE_FAIL <timestamp>`. Silence is not acceptable when the deliverable didn't go out.

## Why the strict failure handling

The whole point of this cron is to email a third party. If something silently fails, the third party doesn't get their content and you don't notice for a day or more. That's why the success path is "must see message_id" and failures shout.
