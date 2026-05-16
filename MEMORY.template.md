# MEMORY.md — Long-term knowledge base

> **Template:** copy to `MEMORY.md` and start populating. Your `MEMORY.md` is gitignored — it stays local.

This is Nolty's persistent memory across sessions. Unlike `memory/YYYY-MM-DD.md` (today's session log), this file holds curated, durable context — things you want her to remember every day.

## Migrating from OpenClaw?

If you're coming from OpenClaw, your old memories live in OC's database. To bring them over:

1. Export your OC memory entries to text (the OC CLI has a dump command — check `oc help memory`).
2. Pick the 50-100 most important entries (not raw activity logs — curated facts).
3. Format them as bullet points under the headings below.

You can also just start fresh — Nolty will build up new memories as you work together.

## What to write here

Memories should be **durable, true, and useful tomorrow**. Examples of good memory entries:

- "Brad's main email is brad@example.com (work). His personal email is brad@personal.com — only check that on Saturdays."
- "Calendar source: Google Calendar — primary calendar only. Skip the 'Family' calendar."
- "Brad's morning routine: gym 6-7am, coffee 7-7:30, deep work block 8-11am. Don't schedule meetings before 9am."
- "When Brad says 'tomorrow' on a Friday, he means Monday. Confirm if ambiguous."

Examples of BAD memory entries (these go in daily memory or git history, not here):

- ~~"Today we talked about Project X."~~ (ephemeral)
- ~~"Fixed the cron-runner bug at 3pm."~~ (commit message, not memory)
- ~~"Brad seemed tired."~~ (judgment, not fact)

## Sections (suggested structure)

### People

- _Names + relationships + how to refer to them_

### Communication preferences

- _How you like updates delivered, what to flag, what to skip_

### Recurring patterns

- _Weekly rituals, deadlines, recurring meetings_

### Critical facts

- _Things you need Nolty to know but won't tell her again_

### What NOT to do

- _Anti-patterns you've corrected before that you don't want repeated_

---

**Keep this file under ~500 lines.** Nolty loads it fresh every session. Bigger = slower and more expensive.

If MEMORY.md grows beyond that, archive old entries to a `memory/archive-YYYY-MM.md` file.
