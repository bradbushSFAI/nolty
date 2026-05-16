# Contributing to Nolty

Thanks for thinking about contributing. This is an early project; rough edges are expected. The goal: a clean, well-tested kit anyone can use to migrate from OpenClaw to Claude Code.

## What I'd love help with

In rough priority order:

1. **Linux port** — systemd user units in place of LaunchAgents. See [docs/PORTING.md](docs/PORTING.md) for the substitution table.
2. **More example skills** — yours might help someone else. Genericize personal data before submitting.
3. **Bug reports** — especially around edge cases in the cron-runner scheduling logic, or recovery scenarios `/nolty-restart` doesn't yet handle.
4. **Docs improvements** — if a doc was confusing when you set up, fix it.
5. **Alt channels** — iMessage, Discord, or Slack as alternatives to Telegram. Would need a new MCP plugin abstraction.

## What's out of scope (for now)

- Multi-user variants (v1 is single-user)
- Native Windows port (WSL2 path is fine to document; native is a lot of work)
- Replacing the cron-runner with a different scheduling library

## Workflow

1. Open an issue first for anything non-trivial. Describes the problem and your proposed approach.
2. Fork the repo, create a branch, push your changes.
3. PR with a clear title + description of what you changed + why.
4. Make sure `pytest tests/` passes.
5. If your change affects docs, update the relevant doc file in the same PR.

## Code style

- Python: PEP-8 ish. The project doesn't run a linter; readable + small wins.
- Shell: bash, set `-eu`, prefer absolute paths for external commands.
- Markdown: GitHub-flavored. Tables, fenced code blocks. Keep individual files under ~300 lines when possible.

## Commit messages

Conventional Commits aren't required but appreciated:

```
feat(cron-runner): add --dry-run flag
fix(heartbeat): handle missing tmux session in STEP 0.5
docs(MIGRATION): clarify gog vs MCP fallback
```

## License

By contributing, you agree your contributions are licensed under the MIT License (same as the project).
