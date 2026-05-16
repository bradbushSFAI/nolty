# Google Sheet setup for `linkedin-post-tracking-inner`

The skill scrapes LinkedIn post analytics into a Google Sheet. You need to set up the sheet first so the cron has somewhere to read from + write to.

## Quick start

1. Open a new [Google Sheet](https://sheets.new)
2. Name it whatever you like — "LinkedIn Tracking" works
3. Add a tab named exactly **`Post Tracking`** (case + spaces matter; the skill references it as `'Post Tracking'!A1:R80`)
4. Import [`post-tracking-template.csv`](post-tracking-template.csv) — File → Import → choose `Replace current sheet`. This gives you the column headers in row 1.
5. Add a row for each post you've already published (so the cron can track them). Leave columns I-R empty — those are filled by the cron on the check date.
6. Copy the Sheet ID from the URL: `https://docs.google.com/spreadsheets/d/`**`<SHEET_ID>`**`/edit#gid=0`

Then in `examples/linkedin-post-tracking-inner/SKILL.md`, replace every `YOUR_SHEET_ID` with the real Sheet ID.

## Column reference

| Col | Field | Source | When filled |
|---|---|---|---|
| A | Post Date | You, manually | When you schedule/publish the post |
| B | Check Date | You, manually | Set to Post Date + 7 days |
| C | Topic | You, manually (or the cron fills it from Obsidian filename) | At post time |
| D | Link | You, manually | After the post goes live |
| E | Type | You, manually | At post time |
| F | Format | You, manually (text/carousel/image/data-image/video) | At post time |
| G | Hook | You, manually (question/stat/story/contrarian) | At post time |
| H | Length | You, manually (short/medium/long) | At post time |
| I | Impressions | **Cron, automatic** | On check date |
| J | Members Reached | **Cron, automatic** | On check date |
| K | Profile Visits | **Cron, automatic** | On check date |
| L | Follower Gain | **Cron, automatic** | On check date |
| M | Reactions | **Cron, automatic** | On check date |
| N | Comments | **Cron, automatic** | On check date |
| O | Reposts | **Cron, automatic** | On check date |
| P | Saves | **Cron, automatic** | On check date |
| Q | Sends | **Cron, automatic** | On check date |
| R | Link Engagement | **Cron, automatic** | On check date |

## Snapshot rule

Once columns I-R have values in a row, **the cron NEVER touches that row again** — it's a historical snapshot. If you want to refresh metrics for a post, manually clear column I and the cron will re-scrape on the next run.

## Workflow

1. **Post day:** Manually fill columns A-H for the new post.
2. **Day 7 after posting:** The cron (`linkedin-post-tracking-{tue,wed,thu}` if you schedule it Tue/Wed/Thu, or whatever cadence you set) finds rows where `Check Date == today AND Impressions is empty`, scrapes LinkedIn, fills I-R.
3. **Done.** That row is now a permanent snapshot.

## Optional: tab for weekly aggregate

The `linkedin-weekly-rollup-inner` example uses a separate tab called `Weekly Detailed Tracking` with columns A=Date, B=Impressions, C=Members Reached, D=Engagements, E=Reactions, F=Comments, G=Reposts, H=Saves, I=Sends, J=Premium Button Clicks. Same Sheet, different tab. Add it if you also use that example.
