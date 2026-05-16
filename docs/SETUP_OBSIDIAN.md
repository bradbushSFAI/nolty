# Setup: Obsidian (or any notes folder)

Several example skills reference `YOUR_OBSIDIAN_VAULT` — `meeting-prep`, `daily-recap`, `linkedin-monthly-analysis`, `content-hour`, etc. This doc explains what they need and how to swap in your own notes folder if you don't use Obsidian.

## What the skills actually need

Any folder full of markdown files. The skills do four things:

1. **Search for existing notes by filename** (e.g. `find <vault> -iname "*<contact>*"`)
2. **Read individual notes** (via the `Read` tool)
3. **Write new notes** to subfolders like `MeetingPreps/` or `Marketing/LinkedIn/`
4. **(Optional)** Build Obsidian wikilinks (`[[filename]]`) into Telegram messages so you can tap to open

Nothing requires Obsidian specifically. The wikilinks are useful if you DO use Obsidian, harmless if you don't.

## If you use Obsidian

1. Find your vault path. If your vault is named "MyVault" and it lives in the default location:

   ```
   ~/Documents/MyVault
   ~/Obsidian/MyVault
   ~/iCloud Drive/MyVault
   ```

   (Wherever you opened the vault from.)

2. Set `YOUR_OBSIDIAN_VAULT` consistently in the skills that use it. Quick sweep:

   ```bash
   cd ~/Documents/CodingProjects/nolty
   grep -rl YOUR_OBSIDIAN_VAULT examples/ skills/
   # then sed -i '' "s|YOUR_OBSIDIAN_VAULT|/Users/yourname/Obsidian/MyVault|g" <each file>
   ```

   Or just edit each skill as you adopt it.

3. Optionally add a row to your `TOOLS.md`:

   ```
   | **Obsidian notes / search** | `find "<vault path>" -iname "*<term>*"` + `Read` — vault lives at `<vault path>` |
   ```

## If you use plain markdown (no Obsidian)

1. Pick a directory where you keep markdown notes — could be:

   ```
   ~/notes/
   ~/Documents/notes/
   ~/Dropbox/notes/
   ```

2. Same substitution — replace `YOUR_OBSIDIAN_VAULT` with that path.

3. The skills' wikilink output (`[[filename]]`) won't link-tap anywhere for you — just treat the filename references as bare names. You can drop the brackets if you prefer.

## If you don't keep any markdown notes

You can still use Nolty — just skip the examples that reference `YOUR_OBSIDIAN_VAULT`. The core skills (`heartbeat`, `cron-management`, `nolty-mood`, `chatgpt-image`) don't need notes at all.

Or use a stub directory:

```bash
mkdir -p ~/nolty-notes/{MeetingPreps,Marketing}
```

And point the skills at `~/nolty-notes`. Nolty will write into the subfolders as she works.

## What about iCloud sync?

If your vault is in iCloud (`~/iCloud Drive/`), `find` and `Read` work fine, but be aware:

- iCloud may evict files locally if you're low on disk — `find` won't see them until they re-download
- Writes flush to iCloud immediately, but other devices may take a few seconds to sync
- For frequent automated writes (like daily-recap dropping a meeting-notes file every day), this is normally fine

## What about Notion or another notes tool?

Nolty's skills assume filesystem access. Notion/Roam/etc. would need API-based replacements:

- Replace `find` + `Read` with API queries
- Replace `Write` with API page creation

Doable but not shipped. If you write one, contribute it back as an alternative example.
