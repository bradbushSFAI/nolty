---
name: linkedin-publish-inner
description: Schedule LinkedIn posts via the native scheduler UI using inherited claude-in-chrome MCP. MANUAL only, not on a cron. EXAMPLE.
---

# LinkedIn Publish (example, manual)

> **EXAMPLE.** Demonstrates Chrome-driven action on a third-party site. **Manual only** — bot-detection makes this unsafe to automate fully.

The user invokes `/linkedin-publish` manually (typically after weekly content drafts are approved). No cron suffix expected.

## Context

- **Drafts folder:** `YOUR_OBSIDIAN_VAULT/Marketing/Content/Planned/`
- **Published folder:** `YOUR_OBSIDIAN_VAULT/Marketing/Content/Published/`
- **Tracking sheet:** `YOUR_SHEET_ID`, sheet `Post Tracking`
- Bot-detection: wait 5-10 seconds between actions; never click rapidly

## Procedure

### STEP 1 — Identify drafts ready to schedule

List files in `Planned/`. Each should have YAML frontmatter with `post_date`, `title`, `format` etc.

Group by date. Confirm with the user which 1-3 drafts to schedule this session.

### STEP 2 — Navigate to LinkedIn

```
mcp__claude-in-chrome__browser_navigate URL: "https://www.linkedin.com/feed/"
```

Wait for page to render. Find the "Start a post" button — click it.

### STEP 3 — For each draft

a. Paste post body into the composer (copy from the markdown file's body, after frontmatter).
b. Click the schedule (clock) icon.
c. Select the post date + time from the calendar/time picker.
d. Confirm schedule.
e. Wait 10 seconds before next draft (bot-detection).

### STEP 4 — Move file from Planned/ to Published/

```bash
mv YOUR_OBSIDIAN_VAULT/Marketing/Content/Planned/{file}.md \
   YOUR_OBSIDIAN_VAULT/Marketing/Content/Published/
```

Update the frontmatter `status: scheduled` → `status: published-scheduled`.

### STEP 5 — Append tracking row in Google Sheet

```bash
/opt/homebrew/bin/gog sheets append "YOUR_SHEET_ID" "'Post Tracking'!A:R" \
  "$(date '+%m/%d/%Y'),...,{post_date},{check_date = post_date + 7},{title},,{type},{format},{hook},{length}"
```

(Adapt the column count to match the sheet.)

### STEP 6 — Telegram summary

```
📅 3 posts scheduled on LinkedIn:
Tue: [title]
Wed: [title]
Thu: [title]

Post tracking rows created. Files moved to Published/.
```

`reply` MCP tool with `chat_id` from `USER.md`. End with `LINKEDIN_PUBLISH_DONE`.

### STEP 7 — Close Chrome tabs

Same tab-cleanup pattern as `linkedin-post-tracking-inner` STEP 7.

## Why manual only

LinkedIn's bot detection is aggressive. A daily automated post scheduler would trigger account-flag heuristics. Even spaced 10s between actions, daily automation looks suspicious. A weekly human-initiated batch is much safer.
