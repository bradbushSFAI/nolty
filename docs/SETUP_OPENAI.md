# Setup: OpenAI API key (for image generation)

The `chatgpt-image` skill (ships in `skills/chatgpt-image/`) uses OpenAI's `gpt-image-2` model to generate images. The `nolty-mood` skill depends on it, and you may want it for your own image-generation work.

This is **optional** — if you don't run `nolty-mood` or generate images, you can skip this entirely.

> **Heads up:** despite being called "ChatGPT image," the skill talks to OpenAI's API, NOT your ChatGPT web account. You need a separate **API key** — your ChatGPT subscription doesn't grant API access.

## What you need

1. An **OpenAI Platform** account (different from your ChatGPT account, though you can sign in with the same email)
2. A funded API balance (image generation costs around $0.04-$0.19 per image depending on resolution and quality)
3. An API key

## Step 1 — Create an OpenAI Platform account

Go to **[platform.openai.com](https://platform.openai.com)** and sign in (or create an account).

Note: this is the API platform, NOT the ChatGPT consumer site (chat.openai.com / chatgpt.com). They share the same login, but billing is separate.

## Step 2 — Add API credits

OpenAI requires a positive balance to call the image API. From the platform dashboard:

1. Go to **Settings → Billing**
2. Add a payment method
3. Add at least $5 in credits (image gen is cheap; $5 lasts a long time)

You can set a hard limit so you don't accidentally rack up a bill.

## Step 3 — Generate an API key

1. Go to **API keys** in the platform dashboard
2. Click **Create new secret key**
3. Give it a name like `nolty` so you can identify it later
4. Choose project scope (your default project is fine)
5. Copy the key — it starts with `sk-...` and is shown only once

**Save the key immediately.** You can't view it again after closing the dialog.

## Step 4 — Add the key to your shell environment

The skill reads `OPENAI_API_KEY` from the environment. Add it to your shell config so it's always available:

```bash
# For zsh (default on macOS Catalina+)
echo 'export OPENAI_API_KEY="sk-...your-key-here..."' >> ~/.zshenv

# For bash
echo 'export OPENAI_API_KEY="sk-...your-key-here..."' >> ~/.bashrc
```

Then reload:

```bash
source ~/.zshenv   # or ~/.bashrc
```

Verify:

```bash
echo $OPENAI_API_KEY
# Should print: sk-...your-key-here...
```

## Step 5 — Test the skill

In any Claude Code session inside the nolty repo, ask:

```
Use the chatgpt-image skill to generate a simple square image of a test pattern. Save to /tmp/test.png.
```

If `OPENAI_API_KEY` is set correctly, you should see a 1024x1024 PNG appear at `/tmp/test.png` within a few seconds.

If you get an error like `KeyError: 'OPENAI_API_KEY'`, the env var isn't visible to the skill's subprocess. Check:

- Did you `source ~/.zshenv` after editing?
- Is the export inside `.zshenv` (loaded for ALL shells) and not just `.zshrc` (interactive only)?
- Run `env | grep OPENAI` to confirm it's exported.

## Cost considerations

- Default image size (1024x1024) costs ~$0.04 per image with gpt-image-2 at standard quality
- Larger sizes (1536x1024 landscape, 1024x1536 portrait) cost ~$0.06-0.08
- `nolty-mood` generates one image per invocation — running it daily would be roughly $1.20/month
- Set a hard monthly limit at the API platform's billing settings if you're worried

## Skipping image generation

If you don't want to set up OpenAI:

1. **Don't enable `nolty-mood`.** It's the only shipped skill that needs image generation.
2. **Use `nano-banana` instead.** It uses Google Gemini (you'd need a Gemini API key instead).
3. **Skip image gen entirely.** Most of Nolty's value (heartbeat, daily summaries, web scraping) doesn't need image generation at all.

## Security

- API keys grant access to your OpenAI account. If leaked, anyone can use your credits.
- `chmod 600 ~/.zshenv` keeps it user-readable only.
- If a key leaks: go to platform.openai.com → API keys → revoke immediately, then issue a new one.
- The OpenAI platform has a "rotate" feature — use it periodically (every 90 days is a good rhythm).
- **Never commit the key to git.** The Nolty `.gitignore` excludes `.env`-style files, but always double-check.
