# Manual Setup — Do This Before Running Anything

Two accounts, two keys, one file. Nothing else.

## 0. Python (required — skip if you already have it)

You need Python 3.9 or newer.

1. Check if you already have it: open a terminal and run `python --version`
2. If that fails, or shows a version below 3.9, download it from https://www.python.org/downloads/
3. On the installer's first screen, check the box that says "Add Python to PATH" before clicking Install
4. Close and reopen your terminal, then run `python --version` again to confirm it worked

## 1. Anthropic API key (required)

Powers the actual pain-point extraction. Without this, the tool will not run at all.

1. Go to https://console.anthropic.com/settings/keys
2. Sign up / log in
3. Create a key, copy it

## Don't want to set up automated fetching yet? Skip it.

`fetch.py` and the YouTube API key are optional conveniences, not a
requirement. You can copy a transcript yourself from YouTube's own "Show
transcript" button, paste it into a `.md` file matching this header, and
the rest of the tool works exactly the same — including asking Claude
Code directly to save a pasted transcript in this format for you:

```
# Video Title Here

**Channel:** Channel Name
**Published:** 2026-01-01
**URL:** https://www.youtube.com/watch?v=VIDEO_ID
**Downloaded:** 2026-01-01

---

## Transcript

Paste the transcript text here.
```

Save it as `transcripts/<any-group-name>/<any-channel-name>/anything.md`.
Comments are optional — without them, the analysis just runs on the
transcript alone. The Anthropic API key below is still required either
way; that's the actual analysis step, not something you can skip.

## 2. YouTube Data API v3 key (optional, but recommended)

Powers comment fetching. Without this, `fetch.py` still works — it just skips comments and analyzes the transcript alone.

1. Go to https://console.cloud.google.com/apis/credentials
2. Create a project (or use an existing one)
3. Enable "YouTube Data API v3" for that project
4. Create an API key, copy it

## 3. Put both keys in a `.env` file

In this folder, create a file named exactly `.env` with:

```
ANTHROPIC_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here
```

Leave the second line out entirely if you're skipping comments.

## 4. Install dependencies

```
pip install -r requirements.txt
```

That's everything. Once `.env` exists and dependencies are installed, the three commands in the README's "Run it" section work end to end with no further setup.
