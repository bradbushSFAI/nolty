#!/usr/bin/env python3
"""
Audible Deals Scanner — runs all configured profiles and generates a digest.

EXAMPLE — adapt to your own taste.

Tracks previously shown books so each day shows fresh picks (7-day rotation).
Saves seen-ASINs to ~/.config/audible-deals/seen_deals.json.

Usage:
  python3 scan_deals.py [--json] [--output FILE] [--reset]

  --json         Print JSON instead of markdown digest.
  --output FILE  Write the digest to FILE instead of stdout.
  --reset        Clear the seen-history tracker so all books are eligible again.

Prerequisites:
  - `audible-deals` Python CLI: pip install audible-deals
  - Authenticate: deals auth login
  - Save your taste profiles via `deals profile save ...` — see
    https://github.com/chauduyphanvu/audible-deals for the CLI docs.
"""

import subprocess
import json
import sys
import os
from collections import defaultdict
from datetime import datetime, timedelta


# =============================================================================
# CONFIG — EDIT THIS BLOCK FOR YOUR OWN TASTE PROFILES
# =============================================================================

# Path to the `deals` binary (audible-deals CLI). Run `which deals` to find yours.
DEALS_BIN = "/Library/Frameworks/Python.framework/Versions/3.14/bin/deals"

# How many books to show per section per day.
PAGE_SIZE = 10

# How many days before a book can rotate back into the digest.
ROTATION_DAYS = 7

# Library cache location — used by series-continuation scans.
LIBRARY_CACHE = os.path.expanduser("~/.config/audible-deals/library_cache.json")
SEEN_FILE = os.path.expanduser("~/.config/audible-deals/seen_deals.json")

# Your scan sections. Each entry produces one section in the digest.
#
# `kind` is one of:
#   "profile"    — runs `deals find --profile <name>`
#   "category"   — runs `deals find --category <id>` for each id in `category_ids`
#   "keyword"    — runs `deals search <keyword> --profile <name>` for each in `keywords`
#   "narrator"   — runs `deals find --profile <name> --narrator "<narrator>"`
#   "series-gap" — finds books in series you're invested in (owns 2+); requires library cache
#
# Customize this list with your own taste profiles.
SECTIONS = [
    # Example: a "sci-fi" profile you saved with `deals profile save sci-fi --max-price 8 ...`
    # {
    #     "name": "🚀 Sci-Fi",
    #     "kind": "profile",
    #     "profile": "sci-fi",
    # },
    # Example: scan multiple Audible category IDs for one section
    # {
    #     "name": "🔍 Detective & Procedural Mysteries",
    #     "kind": "category",
    #     "category_ids": ["18574617011", "18574619011"],  # Police, Traditional Detectives
    #     "min_hours": 8,
    #     "first_in_series_only": True,
    # },
    # Example: keyword-based search (good for genres without clean category IDs)
    # {
    #     "name": "🇬🇧 British Mysteries",
    #     "kind": "keyword",
    #     "profile": "general-mystery",
    #     "keywords": ["British mystery", "London mystery", "UK detective"],
    # },
    # Example: filter by a favorite narrator
    # {
    #     "name": "🎙️ Tim Gerard Reynolds",
    #     "kind": "narrator",
    #     "profile": "any-genre",
    #     "narrator": "Tim Gerard Reynolds",
    # },
    # Example: find deals in series you own multiple books from
    # {
    #     "name": "📖 Series Continuations",
    #     "kind": "series-gap",
    # },
]

# If you don't customize SECTIONS above, the script will exit with a friendly message
# pointing you here. Replace these examples with your own real profiles.

# Whether to filter out dramatized adaptations (most listeners prefer unabridged).
FILTER_DRAMATIZED = True

# =============================================================================
# END CONFIG
# =============================================================================


def load_seen():
    """Load previously shown ASINs with timestamps."""
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            pass
    return {}


def save_seen(seen):
    """Save seen ASINs with timestamps."""
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(seen, f, indent=2)


def prune_seen(seen, days=ROTATION_DAYS):
    """Remove ASINs older than N days so books rotate back in."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    return {k: v for k, v in seen.items() if v.get("last_shown", "") > cutoff}


def filter_dramatized(books):
    """Remove dramatized adaptations."""
    if not FILTER_DRAMATIZED:
        return books
    skip = ["dramatized", "dramatised", "dramatisation", "dramatization"]
    return [
        b for b in books
        if not any(
            s in (b.get("title") or "").lower() or s in (b.get("subtitle") or "").lower()
            for s in skip
        )
    ]


def pick_fresh(books, seen, section_key, count=PAGE_SIZE):
    """Pick up to `count` books not recently shown in this section."""
    fresh = []
    overflow = []
    for b in books:
        asin = b.get("asin", "")
        seen_key = f"{section_key}:{asin}"
        if seen_key not in seen:
            fresh.append(b)
        else:
            overflow.append(b)
        if len(fresh) >= count:
            break

    # If we don't have enough fresh, cycle back to oldest shown
    if len(fresh) < count:
        needed = count - len(fresh)
        overflow.sort(
            key=lambda b: seen.get(
                f"{section_key}:{b.get('asin', '')}", {}
            ).get("last_shown", "")
        )
        fresh.extend(overflow[:needed])

    # Mark all picked as shown
    now = datetime.now().isoformat()
    for b in fresh:
        asin = b.get("asin", "")
        seen_key = f"{section_key}:{asin}"
        seen[seen_key] = {"last_shown": now, "title": b.get("title", "")}

    return fresh


def run_deals(args, timeout=120):
    """Run deals CLI and return parsed JSON output."""
    cmd = [DEALS_BIN] + args + ["--json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        print(f"  Warning: {' '.join(args[:3])}... failed: {e}", file=sys.stderr)
    return []


def scan_profile_section(section):
    """Run `deals find --profile <name>`."""
    return run_deals(["find", "--profile", section["profile"]])


def scan_category_section(section):
    """Run `deals find --category <id>` for each id, dedupe across."""
    deals = []
    for cat_id in section.get("category_ids", []):
        args = [
            "find", "--category", cat_id,
            "--max-price", str(section.get("max_price", 8)),
            "--min-rating", str(section.get("min_rating", 3.5)),
            "--min-ratings", str(section.get("min_ratings", 20)),
            "--sort", "price-per-hour",
            "--skip-owned",
            "--deep",
            "-n", "0",
        ]
        if section.get("min_hours"):
            args += ["--min-hours", str(section["min_hours"])]
        if section.get("first_in_series_only"):
            args += ["--first-in-series"]
        deals.extend(run_deals(args))
    return sorted(dedupe(deals), key=lambda x: x.get("price_per_hour") or 999)


def scan_keyword_section(section):
    """Run `deals search <keyword> --profile <name>` for each keyword, dedupe."""
    deals = []
    profile = section["profile"]
    for keyword in section.get("keywords", []):
        deals.extend(run_deals(["search", keyword, "--profile", profile]))
    return sorted(dedupe(deals), key=lambda x: x.get("price_per_hour") or 999)


def scan_narrator_section(section):
    """Run `deals find --profile <name> --narrator <narrator>`."""
    return run_deals([
        "find",
        "--profile", section["profile"],
        "--narrator", section["narrator"],
    ])


def scan_series_gaps(library_path=None):
    """Find books on sale in series the user owns 2+ books from."""
    if library_path and os.path.exists(library_path):
        with open(library_path) as f:
            books = json.load(f)
    else:
        books = run_deals(["library"])
        if books:
            os.makedirs(os.path.dirname(LIBRARY_CACHE), exist_ok=True)
            with open(LIBRARY_CACHE, "w") as f:
                json.dump(books, f)

    if not books:
        return []

    series = defaultdict(lambda: {"count": 0, "authors": set()})
    for b in books:
        sn = b.get("series_name", "").strip()
        if sn:
            series[sn]["count"] += 1
            for a in b.get("authors", []):
                series[sn]["authors"].add(a)

    invested = {k: v for k, v in series.items() if v["count"] >= 2}

    all_deals = []
    searched_authors = set()
    for sn, info in sorted(invested.items(), key=lambda x: -x[1]["count"])[:20]:
        author = list(info["authors"])[0] if info["authors"] else None
        if not author or author in searched_authors:
            continue
        searched_authors.add(author)
        deals = run_deals([
            "search", author,
            "--author", author,
            "--max-price", "8",
            "--skip-owned",
            "--min-rating", "3.5",
            "--sort", "price-per-hour",
            "-n", "10",
        ])
        for d in deals:
            d["_source_series"] = sn
            d["_source_author"] = author
        all_deals.extend(deals)

    return sorted(dedupe(all_deals), key=lambda x: x.get("price_per_hour") or 999)


def dispatch_section(section):
    """Route a section's scan to the appropriate scanner function."""
    kind = section.get("kind", "profile")
    if kind == "profile":
        return scan_profile_section(section)
    if kind == "category":
        return scan_category_section(section)
    if kind == "keyword":
        return scan_keyword_section(section)
    if kind == "narrator":
        return scan_narrator_section(section)
    if kind == "series-gap":
        return scan_series_gaps(LIBRARY_CACHE)
    print(f"  Warning: unknown section kind '{kind}', skipping {section['name']}", file=sys.stderr)
    return []


def dedupe(deals):
    """Dedupe a list of deals by ASIN."""
    seen_asins = set()
    unique = []
    for d in deals:
        asin = d.get("asin")
        if asin not in seen_asins:
            seen_asins.add(asin)
            unique.append(d)
    return unique


def format_book(b, idx=None):
    """Format a single book for the digest."""
    prefix = f"{idx}. " if idx else "• "
    title = b.get("title", "Unknown")
    authors = ", ".join(b.get("authors", [])[:2])
    price = b.get("price")
    list_price = b.get("list_price")
    hours = b.get("hours", 0) or 0
    pph = b.get("price_per_hour")
    rating = b.get("rating", 0)
    num_ratings = b.get("num_ratings", 0)
    discount = b.get("discount_pct")
    url = b.get("url", "")
    series = b.get("series_name", "")
    series_pos = b.get("series_position", "")

    series_str = f" ({series} #{series_pos})" if series and series_pos else ""
    price_str = f"${price:.2f}" if price else "?"
    list_str = f" (was ${list_price:.0f})" if list_price else ""
    disc_str = f" -{discount:.0f}%" if discount else ""
    pph_str = f"${pph:.2f}/hr" if pph else ""
    hours_str = f"{hours:.1f}hrs"
    rating_str = f"★{rating:.1f} ({num_ratings:,})" if rating else ""

    line = f"{prefix}**{title}**{series_str}\n"
    line += f"  {authors} | {price_str}{list_str}{disc_str} | {hours_str} | {pph_str} | {rating_str}\n"
    line += f"  {url}\n"
    return line


def generate_digest(results):
    """Generate markdown digest from scan results."""
    now = datetime.now().strftime("%A, %B %d, %Y")
    lines = [f"# 📚 Audible Deals Digest — {now}\n"]

    for section_name, books in results.items():
        lines.append(f"\n## {section_name}\n")
        if not books:
            lines.append("No deals found today.\n")
            continue
        for i, b in enumerate(books, 1):
            lines.append(format_book(b, i))

    lines.append(f"\n---\n*Generated by Nolty's Audible Deals Scanner — fresh picks daily, books rotate back after {ROTATION_DAYS} days.*\n")
    return "\n".join(lines)


def main():
    output_json = "--json" in sys.argv
    output_file = None
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]

    if "--reset" in sys.argv:
        if os.path.exists(SEEN_FILE):
            os.remove(SEEN_FILE)
            print("Seen history cleared.", file=sys.stderr)
        return

    if not SECTIONS:
        print("ERROR: SECTIONS is empty. Edit scan_deals.py — see the CONFIG block at the top.", file=sys.stderr)
        print("Uncomment + customize the example sections, or define your own.", file=sys.stderr)
        sys.exit(2)

    seen = prune_seen(load_seen())

    raw_results = {}
    for section in SECTIONS:
        section_name = section["name"]
        print(f"Scanning {section_name}...", file=sys.stderr)
        raw_results[section_name] = dispatch_section(section)

    # Filter dramatized, then apply rotation
    final_results = {}
    for section_name, all_books in raw_results.items():
        filtered = filter_dramatized(all_books)
        section_key = section_name.split("—")[-1].strip().lower().replace(" ", "_")
        final_results[section_name] = pick_fresh(filtered, seen, section_key, PAGE_SIZE)

    save_seen(seen)

    if output_json:
        print(json.dumps(final_results, indent=2, default=str))
    else:
        digest = generate_digest(final_results)
        if output_file:
            with open(output_file, "w") as f:
                f.write(digest)
            print(f"Digest saved to {output_file}", file=sys.stderr)
        else:
            print(digest)


if __name__ == "__main__":
    main()
