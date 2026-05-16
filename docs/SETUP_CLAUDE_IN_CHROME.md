# Setup: claude-in-chrome

`claude-in-chrome` is built into Claude Code — it's an MCP server that lets Claude drive your real signed-in Chrome browser. **It's not a separate install**; you just need Chrome configured to expose its DOM to Claude.

This is required only for skills that interact with web sites you're signed into (LinkedIn examples, Sheets via web UI, etc.). If you don't run any of those, skip this doc.

## Step 1 — Install the Claude Chrome extension

In Chrome:

1. Open the Chrome Web Store
2. Search for "Claude" or follow the link from `claude.ai`
3. Install the official Claude extension
4. Pin it to your toolbar

## Step 2 — Sign into the sites you care about

Whatever site your crons will interact with (LinkedIn, Google Workspace, etc.), make sure you're signed in via Chrome. The extension uses your live session.

## Step 3 — Enable Chrome MCP in Claude Code

In your `~/.claude.json` (or via Claude Code settings):

```json
{
  "claudeInChromeDefaultEnabled": true
}
```

This is on by default in recent Claude Code versions. Verify by running any session and checking that the MCP tools `mcp__claude-in-chrome__*` are listed.

## Step 4 — Test

In Claude Code:

```
mcp__claude-in-chrome__browser_navigate URL: "https://www.linkedin.com/feed/"
```

If you see the LinkedIn feed in your Chrome window, Chrome MCP is working.

## Inheritance: how sub-agents use Chrome

The `claude-in-chrome` MCP server is single-client — only one Claude session can be bonded to Chrome at a time. Nolty's interactive session holds the connection.

When a cron-runner dispatches a job that needs Chrome (like `linkedin-post-tracking-inner`), the slash command fires in Nolty's session, she spawns a Task sub-agent, and **the sub-agent inherits the `claude-in-chrome` MCP connection from its parent.** No special setup needed in the sub-agent — the tools are just available.

This is why you can't run web-driven crons via `claude -p` (headless): the headless process can't grab Chrome because Nolty's interactive session holds it. The whole reason the cron-runner uses tmux dispatch is to keep web jobs running inside Nolty's session where Chrome inheritance works.

## Bot-detection notes

Sites like LinkedIn have aggressive bot detection. Even though you're driving your real signed-in browser:

- Wait 2-3 seconds between every browser action (skills shipped with this rule baked in)
- Don't run high-frequency automation (every-minute scraping = bad)
- Don't run during sleeping hours (3am LinkedIn scrape = bad)
- Use semantic page navigation (`browser_snapshot` to find elements by label) rather than brittle CSS selectors
- For posting/publishing, keep it manual (the `linkedin-publish-inner` example is explicitly NOT a cron)

The shipped examples follow these rules. If you write your own Chrome-driven cron, do the same.

## Common issues

- **Tool calls return "Chrome MCP not available"** — extension is installed but the bridge isn't running. Restart Chrome, then restart Nolty's tmux session.
- **Calls fire but Chrome window doesn't update** — extension is rate-limited or hit a permissions popup. Check the extension's popup for issues.
- **LinkedIn shows you a "captcha / suspicious activity" page** — bot detection triggered. Stop the cron, sign out and back in, wait a day, reduce frequency.
