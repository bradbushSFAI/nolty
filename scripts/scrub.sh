#!/usr/bin/env bash
# scrub.sh — scrub personal data out of your nolty fork before publishing.
#
# Use when you've personalized Nolty extensively and want to share your fork.
# Replaces personal identifiers with placeholders.
#
# Usage:
#   ./scripts/scrub.sh                        # dry-run; show what would change
#   ./scripts/scrub.sh --apply                # actually do it

set -eu

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
NOLTY_HOME=$(cd "$SCRIPT_DIR/.." && pwd)
cd "$NOLTY_HOME"

APPLY=0
if [ "${1:-}" = "--apply" ]; then
    APPLY=1
fi

if [ "$APPLY" -eq 0 ]; then
    echo "🦀 Scrub (DRY RUN) — pass --apply to actually modify files."
else
    echo "🦀 Scrub (APPLY MODE) — files will be modified."
fi
echo ""

# Define scrub patterns: each line is "pattern→replacement".
# Customize this list before running for your own fork.
declare -a PATTERNS=(
    # Emails — set yours here, will be replaced with the placeholder
    # "yourname@example.com|\${USER_EMAIL}"
    # "yourpartner@example.com|\${RECIPIENT_EMAIL}"

    # Telegram chat_id — your numeric ID
    # "1234567890|\${TELEGRAM_CHAT_ID}"

    # LinkedIn handle
    # "your-linkedin-handle|\${LINKEDIN_HANDLE}"

    # Google Sheet IDs
    # "your_sheet_id_44char|YOUR_SHEET_ID"

    # Paths
    # "/Users/yourname/Obsidian Vault|\${OBSIDIAN_VAULT}"
)

# Files NOT to scrub (mostly examples, which already have placeholders)
EXCLUDES=(
    "examples/*"
    "docs/*"
    "*.template.md"
    "LICENSE"
    "assets/*"
    "tests/*"
    ".git/*"
)

build_find_excludes() {
    local args=""
    for e in "${EXCLUDES[@]}"; do
        args="$args -not -path './$e'"
    done
    echo "$args"
}

if [ ${#PATTERNS[@]} -eq 0 ]; then
    echo "⚠️  No scrub patterns defined in $0."
    echo "   Edit the PATTERNS array at the top of this script with YOUR personal identifiers."
    echo "   Then re-run with --apply."
    exit 1
fi

eval "FIND_EXCLUDES=\"$(build_find_excludes)\""

for pat in "${PATTERNS[@]}"; do
    needle="${pat%%|*}"
    replacement="${pat##*|}"

    matches=$(eval "find . -type f $FIND_EXCLUDES -exec grep -l \"$needle\" {} +" 2>/dev/null || true)
    if [ -z "$matches" ]; then
        echo "   (no occurrences of $needle)"
        continue
    fi

    count=$(echo "$matches" | wc -l | tr -d ' ')
    echo "   $needle → $replacement"
    echo "$matches" | sed 's/^/      /'

    if [ "$APPLY" -eq 1 ]; then
        echo "$matches" | while read -r f; do
            sed -i '' "s|$needle|$replacement|g" "$f"
        done
        echo "   ✓ Applied across $count file(s)"
    fi
    echo ""
done

if [ "$APPLY" -eq 0 ]; then
    echo "🦀 Dry run complete. Re-run with --apply to actually modify."
else
    echo "🦀 Scrub complete. Review the diff before committing:"
    echo "   git diff"
fi
