---
name: qmd-reindex
description: Nightly 3am QMD reindex of workspace + Obsidian vector stores. Silent on success. EXAMPLE.
---

# QMD Reindex (example)

> **EXAMPLE.** Demonstrates the silent-on-success cron pattern. Only sends Telegram on failure.

Spawn a Haiku sub-agent if `[cron ...]` suffix present.

## Setup

Install [qmd](https://github.com/...) for local markdown vector search. Configure your collections in `~/.config/qmd/index.yml`.

## Procedure

### STEP 1 — Update indices

```bash
~/.bun/bin/qmd update -c workspace
~/.bun/bin/qmd update -c obsidian
```

### STEP 2 — Refresh embeddings

```bash
~/.bun/bin/qmd embed -c workspace
~/.bun/bin/qmd embed -c obsidian
```

Both update and embed can run sequentially — `qmd` handles locking internally.

### STEP 3 — Report

- **Success — silent.** End the sub-agent with `QMD_OK <timestamp>`. No Telegram.
- **Failure** (qmd binary missing, index corruption, vector store error, non-zero exit): call `reply` MCP with `chat_id` from `USER.md` and a short message (<200 chars) naming the failed step. End with `QMD_FAIL <timestamp>`. The user must know.

## Notes

- This cron runs at 3am — if your Mac is asleep past the 60-min lag window, the cron-runner skips silently. That's correct behavior; the index will rebuild on the next fire.
