# Setup: gog

`gog` is a CLI wrapper for Google APIs (Gmail, Calendar, Sheets, Drive, Docs, Tasks). Nolty's skills use it heavily because it produces clean one-liner bash commands instead of multi-step MCP tool calls.

## Install

```bash
# Install (check the gog repo for the latest install command)
# Example via homebrew, if available:
brew install gog

# Or from source:
# git clone <gog repo> && cd gog && make install
```

Verify:

```bash
which gog
# Expected: /opt/homebrew/bin/gog (or wherever brew/install placed it)

gog --version
```

## Authenticate

```bash
gog auth login --account YOUR_EMAIL@example.com
```

This opens a browser for Google OAuth. After consenting, gog stores credentials locally (typically under `~/.config/gog/`). You can authenticate multiple accounts and select per-command via `--account`.

## Use absolute path in skills

Critical: skills must call gog via absolute path because Task sub-agents get a thin `PATH` that doesn't include `/opt/homebrew/bin`:

```bash
# ✅ Right
/opt/homebrew/bin/gog gmail send --to recipient@example.com ...

# ❌ Wrong — may silently fail in sub-agent
gog gmail send --to recipient@example.com ...
```

All shipped skills use the absolute path. If you write your own skill, follow the same convention.

If your install path differs from `/opt/homebrew/bin/gog`, find and replace across `skills/` and `examples/`:

```bash
GOG_PATH=$(which gog)
grep -rl '/opt/homebrew/bin/gog' skills/ examples/ | \
    xargs sed -i '' "s|/opt/homebrew/bin/gog|$GOG_PATH|g"
```

## MCP alternative

If you don't want to install gog, the shipped skills include MCP-fallback notes pointing to stock claude.ai MCP tools:

- `mcp__claude_ai_Gmail__search_threads` / `mcp__claude_ai_Gmail__create_draft`
- `mcp__claude_ai_Google_Calendar__list_events`
- `mcp__claude_ai_Google_Drive__gsheets_read` / `gsheets_update_cell`

The MCP path requires you to enable the claude.ai Google integration first. The skills work either way — gog is just faster + cleaner.

## Common gog commands used in shipped skills

| Skill use | Command |
|---|---|
| Search unread email | `gog gmail search "is:unread" --limit 10` |
| Send email | `gog gmail send --to X --subject Y --body-file Z` |
| List today's calendar | `gog calendar list --today --account X --json` |
| Read a sheet range | `gog sheets get "<SHEET_ID>" "'Tab'!A1:R80"` |
| Update a single cell | `gog sheets update "<SHEET_ID>" "'Tab'!I5" "<value>"` |

See `gog --help` for the full command list.
