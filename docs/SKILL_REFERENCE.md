# Skill reference

What each shipped skill does, what it depends on, and how to enable / customize. Each skill name links to the file — click to read the procedure.

## Core skills (`skills/`)

### [`cron-management`](../skills/cron-management/SKILL.md)

**Triggers on:** "show crons", "list crons", "next cron", "add a cron", "enable/disable cron X", "delete cron Y", "run cron Z now", "cron status".

**Does:** Natural-language CRUD over `cron-runner/cron-jobs.json`. Validates schedules with croniter. Confirms before destructive actions.

**Depends on:** Python + croniter.

**Personal data to swap:** none. Generic.

---

### [`heartbeat`](../skills/heartbeat/SKILL.md)

**Triggers via:** the `cron-runner` (every 30 min, 24/7). Skill itself gates quiet hours.

**Does:**

1. STEP 0: Time gate — if outside active hours, exit with `QUIET_HOURS`.
2. STEP 0.5: Claude Code version-drift self-heal.
3. STEP 1: Read foundation files to stay grounded.
4. STEP 2: Pull unread email, flag urgent.
5. STEP 3: Check next 60 min of calendar; flag meetings not already reminded.
6. STEP 4: If anything urgent, send ONE concise Telegram via `reply`.
7. STEP 5: Otherwise, exit silently with `HEARTBEAT_OK`.

**Depends on:** `gog` (or claude.ai Gmail/Calendar MCPs), `reply` MCP tool, `tmux`, `lsof`, `~/.local/share/claude/versions/`.

**Personal data to swap:**

- `YOUR_EMAIL@example.com` (in STEP 2 + 3 gog calls) — your email account
- `America/Chicago` (in STEP 0) — your timezone, if different
- Hour bounds (default 7-23) — your active hours

---

### [`nolty-mood`](../skills/nolty-mood/SKILL.md)

**Triggers on:** "how are you feeling", "how's it going Nolty", "what's your mood".

**Does:** Generates a cute Nolty crab image expressing current mood, sends to user with a one-line caption.

**Depends on:** [`chatgpt-image`](../skills/chatgpt-image/SKILL.md) or `nano-banana` skill (image gen), `reply` MCP tool, OpenAI API key (see [SETUP_OPENAI.md](SETUP_OPENAI.md)).

**Personal data to swap:** none. (Customize the creature if you've changed `IDENTITY.md`.)

---

### [`chatgpt-image`](../skills/chatgpt-image/SKILL.md)

**Triggers on:** "generate image", "create a picture", "draw", "make an image of", "chatgpt image", "openai image", "photorealistic image", etc.

**Does:** Generates an image using OpenAI's `gpt-image-2` via API. Supports 1024x1024 / 1536x1024 / 1024x1536 / auto sizes.

**Depends on:** `OPENAI_API_KEY` env var, `uv` (Python runner). See [SETUP_OPENAI.md](SETUP_OPENAI.md) for the full setup including API key creation and billing.

**Personal data to swap:** none. Generic.

---

### [`/nolty-restart`](../.claude/commands/nolty-restart.md) (slash command)

**Triggers on:** user invokes `/nolty-restart` from any Claude Code session.

**Does:** Diagnoses every layer of the Nolty stack (tmux, claude process, version drift, LaunchAgent, persistence symlink, state freshness), applies targeted fixes, re-verifies.

**Depends on:** Just bash + standard macOS tools (`tmux`, `launchctl`, `lsof`, `pgrep`).

**Personal data to swap:**

- `com.<your-rdns>.cron-runner` — your LaunchAgent label
- `$NOLTY_HOME` — set to your nolty/ checkout path (defaults to `~/Documents/CodingProjects/nolty`)

---

## Example skills (`examples/`)

These ship disabled. Copy to `skills/` and customize to enable. Click each skill name to read the procedure.

### [`examples/audible-deals`](../examples/audible-deals/SKILL.md)

Daily script-driven cron pattern. Runs a Python scanner across saved profiles, emails the digest to a chosen recipient via gog.

Depends on: the [`audible-deals`](https://github.com/chauduyphanvu/audible-deals) Python CLI, gog.

### [`examples/morning-brief`](../examples/morning-brief/SKILL.md)

Daily 6:30am multi-source aggregator: calendar + email + meeting prep (via nested sub-agent) + weather + tasks → single rich Telegram message.

Depends on: gog, weather API (wttr.in is free), a meeting-prep sub-skill (you write or omit).

### [`examples/daily-recap`](../examples/daily-recap/SKILL.md)

Daily 9pm end-of-day reconciliation: sent emails, today's meetings, Zoom transcripts (if available), task reconciliation → Telegram summary.

Depends on: gog, your task source.

### [`examples/linkedin-post-tracking-inner`](../examples/linkedin-post-tracking-inner/SKILL.md)

Web scraping via inherited `claude-in-chrome` MCP: read which posts are due to be tracked from a Google Sheet, navigate to each post's LinkedIn analytics page, extract 10 metrics, write back to sheet, send Telegram summary.

Depends on: gog, claude-in-chrome configured, your LinkedIn account.

### [`examples/linkedin-weekly-rollup-inner`](../examples/linkedin-weekly-rollup-inner/SKILL.md)

Weekly Chrome-driven aggregate analytics: 7-day creator analytics + WoW comparison + identify top post → Telegram.

Depends on: same as post-tracking-inner.

### [`examples/linkedin-monthly-analysis`](../examples/linkedin-monthly-analysis/SKILL.md)

1st-of-month read-only analytics: pull a month's tracked posts from sheet, compute aggregates and rankings, write markdown report to Obsidian, Telegram top 3 findings.

Depends on: gog, your Obsidian vault (optional).

### [`examples/content-hour`](../examples/content-hour/SKILL.md)

Weekly interactive content planning: walk idea library, rank candidates, research news hooks, present picks via Telegram, draft each post collaboratively with the user, save to Planned/, write tracking row in sheet.

Depends on: an Obsidian-style content idea library, gog, your platform's formatting conventions.

### [`examples/cc-usage-check`](../examples/cc-usage-check/SKILL.md)

Daily 11:45pm tmux-in-tmux pattern: spawn a nested tmux, run `claude --status`, capture the TUI, parse weekly usage %, compare to projected, Telegram delta.

Depends on: tmux only.

### [`examples/qmd-reindex`](../examples/qmd-reindex/SKILL.md)

Nightly 3am silent-on-success cron: run `qmd update` + `qmd embed` to rebuild your local markdown vector indexes.

Depends on: [qmd](https://github.com/...) installed + configured.

### [`examples/prompt-hygiene-audit`](../examples/prompt-hygiene-audit/SKILL.md)

Weekly Saturday 4am meta-audit: fetch latest Claude prompt-engineering best-practices, read your own slash commands + foundation files, flag drift, write report, Telegram top 3 findings.

Depends on: WebFetch, your config files.

### [`examples/home-loan-rate`](../examples/home-loan-rate/SKILL.md)

Weekly Sunday 4pm single-MCP-call pattern: query Perplexity for current mortgage rates in your region, format, Telegram.

Depends on: Perplexity MCP with API key.

### [`examples/post-memory`](../examples/post-memory/SKILL.md)

Optional external activity-logging pattern. Env-gated: if `ACTIVITY_FEED_URL` is set, POSTs an action+description to that endpoint. Otherwise just appends to today's local memory.

Depends on: an external HTTP endpoint (Supabase, Airtable, Zapier webhook, your own service — pick one).

---

## Customization tips

- **Genericize before enabling.** Replace `YOUR_*` placeholders, swap personal email + Sheet IDs + paths.
- **Test with `--dry-run` first.** Add the cron with `enabled: false`, force-fire via `python3 cron-runner/bin/cron-runner.py fire <id>` to verify, then enable.
- **Lag windows matter.** Daily crons: 60 min. Weekly: 1440 min (1 day). Monthly: 2880 min. Heartbeat: 20 min (tight).
- **Telegram length:** keep under ~1500 chars when possible. Multi-paragraph is fine; multi-screen is not.
- **Failure must be loud.** Every example ends with success OR failure sentinel + reply tool call. Don't add a silent success path.
