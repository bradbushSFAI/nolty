#!/usr/bin/env bash
# preflight-check.sh — verify Nolty's install correctness.
#
# Run after `install.sh` and periodically as a health check.
# Exits non-zero if any check fails.

set -u

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
NOLTY_HOME=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$NOLTY_HOME"

PASS=0
FAIL=0

check() {
    local desc="$1"
    local cmd="$2"
    local fix="$3"
    if eval "$cmd" >/dev/null 2>&1; then
        echo "   ✓ $desc"
        PASS=$((PASS+1))
    else
        echo "   ✗ $desc"
        echo "     fix: $fix"
        FAIL=$((FAIL+1))
    fi
}

echo "🦀 Nolty preflight"
echo "   NOLTY_HOME=$NOLTY_HOME"
echo ""

# --- Environment -------------------------------------------------------------
echo "Environment:"
check "Python 3.9+" \
    'python3 -c "import sys; assert sys.version_info >= (3,9)"' \
    "brew install python (or upgrade existing)"

check "croniter importable" \
    "python3 -c 'import croniter'" \
    "pip3 install croniter"

check "tmux installed" \
    "command -v tmux" \
    "brew install tmux"

check "claude CLI installed" \
    "command -v claude || [ -x \"\$HOME/.local/bin/claude\" ]" \
    "install Claude Code (https://claude.ai/code)"

check "gog CLI installed (optional but recommended)" \
    "command -v gog" \
    "see docs/SETUP_GOG.md"

echo ""

# --- Repo structure ----------------------------------------------------------
echo "Repo structure:"
check "CLAUDE.md present" \
    "[ -f CLAUDE.md ]" \
    "git clone the repo correctly"

check "cron-runner.py executable" \
    "[ -x cron-runner/bin/cron-runner.py ]" \
    "chmod +x cron-runner/bin/cron-runner.py"

check "clawd-restart.sh executable" \
    "[ -x clawd-restart.sh ]" \
    "chmod +x clawd-restart.sh"

check "send-telegram.sh executable" \
    "[ -x cron-runner/bin/send-telegram.sh ]" \
    "chmod +x cron-runner/bin/send-telegram.sh"

check "cron-jobs.json present (or example exists)" \
    "[ -f cron-runner/cron-jobs.json ] || [ -f cron-runner/cron-jobs.example.json ]" \
    "cp cron-runner/cron-jobs.example.json cron-runner/cron-jobs.json"

if [ -f cron-runner/cron-jobs.json ]; then
    check "cron-jobs.json parses as valid JSON" \
        "python3 -c 'import json; json.load(open(\"cron-runner/cron-jobs.json\"))'" \
        "fix JSON syntax — try python3 -m json.tool cron-runner/cron-jobs.json"
fi

check "cron-runner state directory writable" \
    "touch cron-runner/state/.preflight && rm cron-runner/state/.preflight" \
    "chmod -R u+w cron-runner/state/"

check "cron-runner logs directory writable" \
    "touch cron-runner/logs/.preflight && rm cron-runner/logs/.preflight" \
    "chmod -R u+w cron-runner/logs/"

echo ""

# --- Foundation files --------------------------------------------------------
echo "Foundation files:"
for f in USER.md MEMORY.md IDENTITY.md SOUL.md TOOLS.md HEARTBEAT.md AGENTS.md; do
    if [ -f "$f" ]; then
        echo "   ✓ $f"
        PASS=$((PASS+1))
    else
        echo "   ⚠️  $f — not yet customized"
        echo "      fix: cp ${f%.md}.template.md $f"
    fi
done
echo ""

# --- LaunchAgent -------------------------------------------------------------
echo "LaunchAgent:"
PLIST_LINK=$(ls "$HOME/Library/LaunchAgents/" 2>/dev/null | grep -E '\.cron-runner\.plist$' | head -1)
if [ -n "$PLIST_LINK" ]; then
    echo "   ✓ plist symlinked: $PLIST_LINK"
    PASS=$((PASS+1))
    LABEL="${PLIST_LINK%.plist}"

    if launchctl list 2>/dev/null | grep -q "$LABEL"; then
        echo "   ✓ LaunchAgent loaded: $LABEL"
        PASS=$((PASS+1))
    else
        echo "   ✗ LaunchAgent NOT loaded: $LABEL"
        echo "     fix: launchctl bootstrap gui/\$(id -u) $HOME/Library/LaunchAgents/$PLIST_LINK"
        FAIL=$((FAIL+1))
    fi
else
    echo "   ✗ no cron-runner plist in ~/Library/LaunchAgents/"
    echo "     fix: run ./scripts/install.sh"
    FAIL=$((FAIL+1))
fi
echo ""

# --- Telegram ----------------------------------------------------------------
echo "Telegram:"
TG_ENV="${TELEGRAM_ENV_FILE:-$HOME/.claude/channels/telegram/.env}"
check "$TG_ENV exists" \
    "[ -f \"$TG_ENV\" ]" \
    "see docs/SETUP_TELEGRAM.md to create it"

if [ -f "$TG_ENV" ]; then
    if grep -q '^TELEGRAM_BOT_TOKEN=' "$TG_ENV"; then
        echo "   ✓ TELEGRAM_BOT_TOKEN set"
        PASS=$((PASS+1))
    else
        echo "   ✗ TELEGRAM_BOT_TOKEN missing in $TG_ENV"
        FAIL=$((FAIL+1))
    fi
    if grep -q '^TELEGRAM_CHAT_ID=' "$TG_ENV"; then
        echo "   ✓ TELEGRAM_CHAT_ID set"
        PASS=$((PASS+1))
    else
        echo "   ✗ TELEGRAM_CHAT_ID missing in $TG_ENV"
        FAIL=$((FAIL+1))
    fi
fi
echo ""

# --- Tmux session (only an issue if Nolty should be running) -----------------
echo "Tmux session (informational):"
if tmux has-session -t CC_running_like_OC 2>/dev/null; then
    echo "   ✓ CC_running_like_OC tmux session is live"
    PASS=$((PASS+1))
else
    echo "   ℹ️  CC_running_like_OC tmux session not running"
    echo "      (start with ./clawd-restart.sh when you want Nolty live)"
fi
echo ""

# --- Summary -----------------------------------------------------------------
echo "Summary: $PASS pass, $FAIL fail"
echo ""

if [ "$FAIL" -gt "0" ]; then
    echo "❌ preflight has $FAIL issue(s). Fix above and re-run."
    exit 1
else
    echo "✅ preflight clean."
    exit 0
fi
