#!/usr/bin/env bash
# install.sh — one-shot Nolty setup script.
#
# Idempotent: safe to re-run. Verifies prerequisites, symlinks the LaunchAgent
# plist into ~/Library/LaunchAgents/ for boot persistence, and bootstraps it.
#
# Usage:
#   ./scripts/install.sh

set -eu

# --- Locate the repo ---------------------------------------------------------
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
NOLTY_HOME=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$NOLTY_HOME"

echo "🦀 Nolty install"
echo "   NOLTY_HOME=$NOLTY_HOME"
echo ""

# --- Step 1: prerequisites ---------------------------------------------------
echo "[1/5] Checking prerequisites..."

missing=0

if ! command -v python3 >/dev/null 2>&1; then
    echo "   ✗ python3 not found. Install Python 3.9+ (brew install python)."
    missing=1
else
    pyver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "   ✓ python3 $pyver"
fi

if ! python3 -c "import croniter" 2>/dev/null; then
    echo "   ⚠️  croniter not installed for $(which python3). Installing..."
    pip3 install croniter || {
        echo "   ✗ croniter install failed. Run: pip3 install croniter"
        missing=1
    }
fi

if ! command -v tmux >/dev/null 2>&1; then
    echo "   ✗ tmux not found. Install: brew install tmux"
    missing=1
else
    echo "   ✓ tmux $(tmux -V | awk '{print $2}')"
fi

if ! command -v claude >/dev/null 2>&1 && ! [ -x "$HOME/.local/bin/claude" ]; then
    echo "   ✗ claude CLI not found. Install Claude Code first."
    missing=1
else
    echo "   ✓ claude CLI found"
fi

if ! command -v gog >/dev/null 2>&1; then
    echo "   ⚠️  gog not found. Some examples won't work without it."
    echo "      See docs/SETUP_GOG.md"
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "   ⚠️  uv not found. The chatgpt-image skill (image generation) requires it."
    echo "      Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

if [ "$missing" -ne "0" ]; then
    echo ""
    echo "❌ Missing prerequisites — fix the above and re-run."
    exit 1
fi

echo ""

# --- Step 2: pick a LaunchAgent label ----------------------------------------
echo "[2/5] LaunchAgent label..."

# Default label; user can override via env var
LABEL="${NOLTY_LABEL:-com.example.cron-runner}"
echo "   Using label: $LABEL"
if [ "$LABEL" = "com.example.cron-runner" ]; then
    echo "   ⚠️  Default label. To customize: set NOLTY_LABEL env var and re-run."
fi
echo ""

# --- Step 3: render the plist from template ----------------------------------
echo "[3/5] Rendering LaunchAgent plist..."

PLIST_SRC="$NOLTY_HOME/cron-runner/com.example.cron-runner.plist.template"
PLIST_OUT="$NOLTY_HOME/cron-runner/$LABEL.plist"

if [ ! -f "$PLIST_SRC" ]; then
    echo "   ✗ Template not found: $PLIST_SRC"
    exit 1
fi

# Substitute placeholders
PYTHON_BIN=$(which python3)
sed -e "s|com\.example\.cron-runner|$LABEL|g" \
    -e "s|/Users/YOUR_USER/Documents/CodingProjects/nolty|$NOLTY_HOME|g" \
    -e "s|/Library/Frameworks/Python.framework/Versions/3.11/bin/python3|$PYTHON_BIN|g" \
    "$PLIST_SRC" > "$PLIST_OUT"

echo "   ✓ Wrote $PLIST_OUT"
echo ""

# --- Step 4: symlink into ~/Library/LaunchAgents/ ----------------------------
echo "[4/5] Installing into ~/Library/LaunchAgents/ (boot persistence)..."

mkdir -p "$HOME/Library/LaunchAgents"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"
ln -sf "$PLIST_OUT" "$TARGET"
echo "   ✓ Symlinked $TARGET"
echo ""

# --- Step 5: bootstrap LaunchAgent -------------------------------------------
echo "[5/5] Loading LaunchAgent..."

# Unload if already loaded (idempotent)
if launchctl list 2>/dev/null | grep -q "^[^[:space:]]*[[:space:]][^[:space:]]*[[:space:]]$LABEL$"; then
    echo "   Unloading existing instance..."
    launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
fi

# Bootstrap
launchctl bootstrap "gui/$(id -u)" "$TARGET"

# Verify
if launchctl list 2>/dev/null | grep -q "$LABEL"; then
    echo "   ✓ LaunchAgent loaded: $LABEL"
else
    echo "   ✗ Bootstrap appeared to fail. Check 'launchctl list | grep cron-runner'."
    exit 1
fi

echo ""
echo "🦀 Install complete."
echo ""
echo "Next steps:"
echo "  1. Copy templates to live files (if you haven't):"
echo "       for f in USER MEMORY IDENTITY SOUL TOOLS HEARTBEAT AGENTS; do"
echo "         cp \$f.template.md \$f.md"
echo "       done"
echo "       cp cron-runner/cron-jobs.example.json cron-runner/cron-jobs.json"
echo ""
echo "  2. Set up your Telegram bot — see docs/SETUP_TELEGRAM.md"
echo ""
echo "  3. Edit USER.md (your email, chat_id, timezone, etc.)"
echo ""
echo "  4. Start Nolty's tmux session:"
echo "       ./clawd-restart.sh"
echo ""
echo "  5. Verify everything:"
echo "       ./scripts/preflight-check.sh"
