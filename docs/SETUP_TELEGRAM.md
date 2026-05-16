# Setup: Telegram

Nolty's main interface is Telegram. You'll need:

1. A Telegram bot (free, ~3 min via BotFather)
2. Your numeric chat_id
3. The `telegram@claude-plugins-official` plugin enabled
4. An `.env` file with the bot token + chat_id (for the emergency fallback script)

## Step 1 — Create the bot

1. Open Telegram, search for **@BotFather**, start a chat.
2. Send `/newbot`.
3. BotFather asks for a name (display name). Use whatever you like — "Nolty" is fine.
4. BotFather asks for a username. Must end in `bot`. E.g. `MyNoltyBot`.
5. BotFather replies with a token like `1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`. **Save this — it's a password.**

## Step 2 — Find your chat_id

You have a few options:

- **Easy:** Search for **@userinfobot** in Telegram, start the chat, it replies with your user ID. That number is your chat_id.
- **Manual:** message your new bot once (any text). Then visit `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser. Look for `"chat":{"id":1234567890,...}`. That number is your chat_id.

## Step 3 — Save token + chat_id

Create `~/.claude/channels/telegram/.env`:

```bash
mkdir -p ~/.claude/channels/telegram
cat > ~/.claude/channels/telegram/.env <<EOF
TELEGRAM_BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=1234567890
EOF
chmod 600 ~/.claude/channels/telegram/.env
```

The `.env` file is used by `cron-runner/bin/send-telegram.sh` (emergency fallback only). The plugin itself reads the token from its own config — see step 4.

## Step 4 — Install the Telegram plugin

```bash
claude plugins install telegram@claude-plugins-official
```

The plugin will prompt for the bot token on first use. Paste in the same token from step 1.

Verify it's enabled:

```bash
# In TelegramConfig/, should print "true"
cat /path/to/nolty/TelegramConfig/.claude/settings.json
```

## Step 5 — Add your chat_id to USER.md

Open `USER.md` (after you've copied from `USER.template.md`) and set:

```
Your chat_id: 1234567890
```

The skills use this for the `reply` MCP tool's `chat_id` parameter.

## Step 6 — Test inbound + outbound

1. Run `./clawd-restart.sh` to launch Nolty's tmux session.
2. Send your bot a message: "Hi Nolty, what's your name?"
3. Wait ~5-15 seconds. You should get a reply.

If no reply, check:

- `tmux attach -t CC_running_like_OC` — is the claude process visible?
- Is there a `❯ <your message>` line in the pane? (means plugin received but not processed)
- Is the plugin loaded? In the pane: `/doctor`

## Common issues

- **"118 skill descriptions dropped" warning** — harmless; plugin marketplace just has more skill files than CC's budget. Doesn't break anything.
- **Plugin says "telegram: not connected"** — token is wrong. Re-paste in step 4.
- **You see your message in the pane but no reply** — the bun subprocess is alive but the claude binary may have version-drift. Run `/nolty-restart` from any Claude Code session.

## Security

- The `.env` file has your bot token. `chmod 600` keeps it user-readable only.
- Bot tokens grant full bot control. If leaked, anyone can send messages AS your bot (not from you).
- The plugin already enforces a chat_id allowlist — only messages from the chat_id in your config are processed. Random people who find your bot's username and message it will be ignored.
- If your bot's token leaks, regenerate immediately: BotFather → `/token` → select your bot → confirm.
