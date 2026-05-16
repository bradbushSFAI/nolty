# USER.md — About You

> **Template:** copy this file to `USER.md`, then fill in the placeholders below. Your `USER.md` is gitignored — it stays local. This file is what Nolty loads on every session start to know who she's working with.

## Who you are

- **Name:** _Your name_
- **Email:** _your-email@example.com_
- **Company:** _Your company / role_
- **Timezone:** _e.g. America/Chicago_
- **Active hours (CT):** _e.g. 7:00 AM – 11:00 PM_ — Nolty's heartbeat will respect these; outside this window, she sends `QUIET_HOURS` and exits.

## How you like to work

- **Communication style:** _e.g. direct, dry, low-emoji_
- **Output preference:** _e.g. terse status updates, no trailing summaries_
- **Decision style:** _e.g. show me the tradeoff, let me pick_
- **What you DON'T want:** _e.g. don't apologize for partial answers, don't speculate without data_

## Important relationships / accounts

- _List any people Nolty should know about (family, key clients, frequent collaborators) so she can flag relevant emails / calendar events._
- _List any email accounts she should check (work, personal) and which is primary._

## Telegram

- **Bot token:** stored at `~/.claude/channels/telegram/.env` (set this up via BotFather — see `docs/SETUP_TELEGRAM.md`)
- **Your chat_id:** _Your Telegram numeric user ID, e.g. 1234567890_

## Personal patterns / rules

_Free-form. Anything you'd tell a new assistant about how to work with you. Examples:_

- _"Always confirm before sending external emails on my behalf."_
- _"Don't suggest meetings before 9am."_
- _"My 'work week' is Monday-Thursday."_

---

**This file is loaded fresh every time Nolty starts a session.** Keep it under 200 lines for context efficiency.
