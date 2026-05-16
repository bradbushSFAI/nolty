#!/bin/bash
# send-telegram.sh — Emergency Telegram alert via Telegram Bot API.
#
# Used ONLY for "Nolty is down" alerts when the plugin's bun process
# has died and the in-session `reply` MCP tool isn't reachable.
#
# For normal cron telegram output, skills use the `reply` MCP tool —
# this script is the fallback of last resort.
#
# Setup: create ~/.claude/channels/telegram/.env with:
#   TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
#   TELEGRAM_CHAT_ID=1234567890
#
# Usage:
#   ./send-telegram.sh "Your message text"

set -eu

MSG="${1:-}"
if [ -z "$MSG" ]; then
    echo "Usage: $0 <message>" >&2
    exit 2
fi

ENV_FILE="${TELEGRAM_ENV_FILE:-$HOME/.claude/channels/telegram/.env}"
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found. See docs/SETUP_TELEGRAM.md." >&2
    exit 3
fi

# shellcheck disable=SC1090
. "$ENV_FILE"

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
    echo "ERROR: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in $ENV_FILE" >&2
    exit 4
fi

curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "parse_mode=Markdown" \
    --data-urlencode "text=${MSG}" > /dev/null
