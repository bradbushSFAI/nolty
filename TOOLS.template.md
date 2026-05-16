# TOOLS.md — Tool reference

> **Template:** copy to `TOOLS.md` and customize for your setup. Nolty reads this on session start so she knows which tool to reach for first.

## Quick reference: which tool for what

| Task | Tool |
|------|------|
| **Web search** | `mcp__perplexity__perplexity_search` (if Perplexity MCP configured) or `WebSearch` tool |
| **Fetch URL content** | `WebFetch` tool |
| **Browse websites (with auth)** | `claude-in-chrome` MCP — uses your live Chrome session |
| **Read/write local files** | `Read` / `Write` / `Edit` tools |
| **Google Sheets** | `/opt/homebrew/bin/gog sheets` CLI — see [gog setup](docs/SETUP_GOG.md) |
| **Gmail** | `/opt/homebrew/bin/gog gmail` CLI |
| **Google Calendar** | `/opt/homebrew/bin/gog calendar` CLI |
| **Google Drive** | `/opt/homebrew/bin/gog drive` CLI |
| **Telegram (outbound)** | `reply` MCP tool (from `telegram@claude-plugins-official` plugin) |
| **Run scheduled work** | `cron-runner` types `/slash-command` into your tmux pane |
| **Long-running tasks** | Spawn a Task sub-agent — keeps the main thread free |
| **Image generation** | `chatgpt-image` skill (OpenAI gpt-image-2; requires `OPENAI_API_KEY` env var — see `docs/SETUP_OPENAI.md`) |
| **Workspace + Obsidian semantic search** | `qmd query "<phrase>" -c workspace` (or `-c obsidian`) — only if you've installed [qmd](https://github.com/...) |
| **Weather (quick one-liner)** | `curl -s "wttr.in/<YOUR_CITY>?format=3"` — free, no auth |
| **Activity logging** | `post-memory` skill — only if you've enabled an external activity feed (`ACTIVITY_FEED_URL` env var) |

## Rules for tool selection

### Always use absolute paths for external CLIs

Task sub-agents get a minimal `PATH`. The shell that runs Bash tool commands does NOT have `/opt/homebrew/bin` by default. So instead of:

```bash
gog gmail send --to ...    # ❌ may fail silently in sub-agent
```

Use:

```bash
/opt/homebrew/bin/gog gmail send --to ...    # ✅ works in any sub-agent
```

This rule cost Brad a missed email digest to a real recipient in May 2026. Don't repeat it.

### Use `reply` MCP tool for Telegram, not shell scripts

The Telegram plugin is loaded in Nolty's interactive session and inherited by all Task sub-agents. The `reply` tool with `chat_id: <your_id>` is always available.

Do NOT use any `send-telegram.sh` style fallback — that path is for emergency use only (when the plugin's bun process has died and you need to surface a "Nolty is down" alert).

### Prefer MCP tools when available

For Google APIs specifically:

- **gog** is faster and produces cleaner one-line bash commands. Use it by default in skills.
- **Stock claude.ai MCPs** (`mcp__claude_ai_Gmail__*`, `mcp__claude_ai_Google_Calendar__*`, `mcp__claude_ai_Google_Drive__gsheets_*`) are an alternative if you don't want to install gog.

Pick one path and stick with it. Mixing in a single skill leads to confusing error modes.

## Optional tools (only if you use them)

| Tool | Used by | Install |
|------|---------|---------|
| `qmd` | Workspace + Obsidian vector search | `brew install qmd` (bun-based) |
| `audible-deals` | Audible scanner script | `pip install audible-deals` |
| `nano-banana` skill | Gemini image generation | Built into Claude Code |
| `chatgpt-image` skill | OpenAI gpt-image-2 generation | Built into Claude Code |

Add your own tooling rows here as you adopt them.

---

This file is loaded fresh every session. Keep under ~200 lines.
