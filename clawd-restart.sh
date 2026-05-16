#!/bin/bash
# clawd-restart.sh — Restart Nolty's Claude Code Telegram listener in tmux.
#
# Usage:
#   ./clawd-restart.sh
#
# Customize NOLTY_HOME below if you cloned to a non-standard location.

set -u

# --- Edit these to match your setup -----------------------------------------
NOLTY_HOME="${NOLTY_HOME:-/Users/$USER/Documents/CodingProjects/nolty}"
CLAUDE_BIN="${CLAUDE_BIN:-$HOME/.local/bin/claude}"
TMUX_BIN="${TMUX_BIN:-$(command -v tmux)}"
TMUX_SESSION="${TMUX_SESSION:-CC_running_like_OC}"
MODEL="${NOLTY_MODEL:-claude-opus-4-6}"
PLUGIN="${NOLTY_PLUGIN:-plugin:telegram@claude-plugins-official}"
LOG_FILE="${NOLTY_LOG:-/tmp/nolty.log}"
# ----------------------------------------------------------------------------

PROJECT_DIR="$NOLTY_HOME/TelegramConfig"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE" >&2
}

log "=== nolty restart triggered ==="

# Kill any zombie telegram bot subprocesses
log "Killing existing Telegram bot processes..."
pkill -f 'telegram.*start' 2>/dev/null
sleep 1
remaining=$(pgrep -f 'telegram.*start' | wc -l | tr -d ' ')
if [ "$remaining" -gt "0" ]; then
    log "Force-killing $remaining stubborn process(es)..."
    pkill -9 -f 'telegram.*start' 2>/dev/null
    sleep 1
fi

# Kill existing tmux session
if "$TMUX_BIN" has-session -t "$TMUX_SESSION" 2>/dev/null; then
    log "Killing existing tmux session: $TMUX_SESSION"
    "$TMUX_BIN" kill-session -t "$TMUX_SESSION" 2>/dev/null
    sleep 1
fi

# Verify project dir
if [ ! -d "$PROJECT_DIR" ]; then
    log "ERROR: PROJECT_DIR not found: $PROJECT_DIR"
    log "Set NOLTY_HOME to your nolty/ checkout path."
    exit 2
fi

# Start fresh tmux session
log "Starting tmux session in $PROJECT_DIR"
"$TMUX_BIN" new-session -d -s "$TMUX_SESSION" -c "$PROJECT_DIR"

# Launch Claude Code with the Telegram channel.
# --permission-mode bypassPermissions covers all tool categories including MCP.
log "Launching Claude Code with Telegram channel..."
"$TMUX_BIN" send-keys -t "$TMUX_SESSION" \
    "unset CLAUDECODE && $CLAUDE_BIN --model $MODEL --channels $PLUGIN --permission-mode bypassPermissions --dangerously-skip-permissions" Enter

log "=== restart complete (Claude Code booting in tmux) ==="
