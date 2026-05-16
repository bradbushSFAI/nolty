# Customizing Nolty

Nolty ships as "an orange crab" by default — but the persona is yours to change. This doc walks you through tailoring the agent to fit your own brand or vibe.

## What you can customize

### Identity (creature, name, look)

Edit `IDENTITY.md`:

- **Name:** swap "Nolty" for whatever you want. Pick something memorable. Single word is best.
- **Creature:** swap "orange crab" for any animal/character. The visual sticks; the brand survives Claude version upgrades.
- **Vibe:** the warm-but-not-effusive default is one option. Adjust to match your personality.

### Visual

Replace `assets/nolty.png` with a new mascot image. Easy way:

```
Use the `chatgpt-image` or `nano-banana` skill:
"Generate a [your creature] mascot for [your agent name]. [Style notes]. Save to assets/nolty.png."
```

Examples that work:

- "Wise old owl wearing spectacles, holding a fountain pen, perched on a stack of books"
- "Compact friendly robot with a single round eye, holding a coffee cup, sitting on a desk"
- "Cartoon raccoon engineer with a hard hat and clipboard"

The mascot appears in the README. Update the README image alt text + size if you want.

### Behavioral defaults

Edit `SOUL.md`:

- **Hard rules.** Quiet-hours timezone, confirmation-required actions, what to never do.
- **Communication style.** Short vs verbose, emoji usage, formality.
- **Tone.** Dry, friendly, terse, formal — your call.

### Reading order

`CLAUDE.md` defines what files Nolty reads on session start, in order. If you have fewer or different foundation files, edit the list.

## What you should NOT change (unless you know what you're doing)

- **`CLAUDE.md`'s "Cron Dispatch Routing" section.** The cron-runner depends on this rule to keep the main thread responsive.
- **`heartbeat/SKILL.md`'s STEP 0.5** version-drift check. This is the autonomous self-heal — disabling it means the system silently dies on CC auto-upgrade.
- **`/nolty-restart`'s component checks.** They mirror the actual install — if you simplify them, recovery can miss real failures.
- **The TelegramConfig subfolder pattern.** Without it, opening the repo in an IDE spawns a duplicate listener.

## Rebranding for a team / company

If you want to ship a customized Nolty as your team's internal tool:

1. Fork the repo
2. Replace `Nolty` with your name everywhere (search-and-replace in `*.md`, `*.template.md`, `CLAUDE.md`)
3. Replace the mascot image with your brand
4. Replace `assets/sfai-logo.png` with your logo
5. Update the README's "Built by" section
6. Decide on a new LaunchAgent label (e.g. `com.yourcompany.cron-runner`) and update `cron-runner/com.example.cron-runner.plist.template` accordingly
7. Update `clawd-restart.sh`'s default `NOLTY_HOME` path

That's roughly half a day of focused work. You can keep the upstream MIT license — just add your modifications notice.

## Changing tmux session name

The default is `CC_running_like_OC` (homage to the OpenClaw migration story). To change:

1. Edit `clawd-restart.sh` → `TMUX_SESSION=YourNewName`
2. Edit `cron-runner/bin/cron-runner.py` → search for `CC_running_like_OC` and replace
3. Edit `/nolty-restart.md` and `heartbeat/SKILL.md` → same search/replace
4. Restart Nolty: `./clawd-restart.sh`

## Adding your own skills

1. Create a folder under `skills/your-skill-name/`
2. Write a `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: your-skill-name
   description: One line; describes what triggers this skill and what it does.
   ---
   ```
3. Write the procedure inline (markdown body). See `skills/heartbeat/SKILL.md` for a full reference.
4. If it's a cron, add to `cron-jobs.json` (or ask Nolty: "add a cron that runs /your-skill-name at 8am daily").

## Adding your own slash commands

Slash commands live in `~/.claude/commands/<name>.md`. The format is the same as a SKILL.md (frontmatter + body).

## Suggested first customizations

If you're new to this:

1. Just rename: `IDENTITY.md` → call her something other than Nolty.
2. Set your active hours in `USER.md` (not 7am-11pm if you're a night owl).
3. Pick 2-3 examples from `examples/` that match your workflow, copy to `skills/`, customize, enable.
4. Leave everything else alone for the first month.

After a month, you'll know which patterns matter to you, and customizing further is easier.
