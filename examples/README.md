# `examples/` — pattern library

The skills in this directory are real, working cron skills from the original Nolty install — genericized so you can adapt them to your own setup.

**They're not enabled by default.** Each one demonstrates a specific pattern. To use one:

1. Read the skill's `SKILL.md` to understand the pattern
2. Copy the skill folder to `skills/`
3. Replace placeholders with your real values
4. Add an entry to `cron-runner/cron-jobs.json` to schedule it

## What pattern each example demonstrates

| Example | Pattern |
|---|---|
| **audible-deals** | Daily Python-script-driven cron that emails a digest. Pattern: script + email + dedup-via-state-file. |
| **morning-brief** | Daily multi-source aggregator (calendar + email + tasks + weather) → Telegram report. Pattern: gog calls + meeting-prep sub-agent nesting + Markdown report format. |
| **daily-recap** | End-of-day reconciliation pulling from many sources. Pattern: read many → synthesize → Telegram. |
| **linkedin-post-tracking-inner** | Web scraping via inherited `claude-in-chrome` MCP. Pattern: read sheet → navigate web → extract metrics → write back to sheet. |
| **linkedin-weekly-rollup-inner** | Same Chrome pattern + WoW comparison computation. |
| **linkedin-monthly-analysis** | Read-only monthly analytics from Google Sheet + Obsidian report write. |
| **content-hour** | Weekly interactive content planning. Pattern: file-walk + ranking + interactive draft + Telegram. The most complex example. |
| **cc-usage-check** | tmux-in-tmux pattern: spawn a nested tmux to capture a TUI screen, parse output. |
| **qmd-reindex** | Silent-on-success cron. Pattern: run a CLI tool, only telegram on failure. |
| **prompt-hygiene-audit** | Weekly meta-audit: read your own slash commands + memory and suggest improvements. |
| **home-loan-rate** | Weekly Perplexity query + Telegram summary. Pattern: single MCP call + format. |
| **post-memory** | Activity logging to an external endpoint. Pattern: HTTP POST with secret-in-env. |

## Genericization

Each example replaces personal identifiers with placeholders:

- `YOUR_EMAIL` — your email account
- `YOUR_CHAT_ID` — your Telegram chat_id (probably `8480842816`-shaped)
- `YOUR_OBSIDIAN_VAULT` — path to your Obsidian Vault, if you have one
- `YOUR_SHEET_ID` — your Google Sheet ID
- `YOUR_LINKEDIN_HANDLE` — your LinkedIn URL slug
- `${REGION}` — geographic region (Dallas-Fort Worth in the original)
- `${RECIPIENT_EMAIL}` — for digest-emailing examples

When you adapt an example, swap these for real values before enabling the cron.

## Caveats

- **MoltyBoard/Supabase references** in the original have been stripped. If you want activity logging, see `examples/post-memory/`.
- **Brad's specific voice/positioning** in `examples/content-hour` and `examples/linkedin-post` has been replaced with generic placeholders — you'll inject your own brand.
- Many examples assume `gog` is installed (see `docs/SETUP_GOG.md`).
