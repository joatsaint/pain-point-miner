# Manual Setup — Do This Before Running Anything

Two accounts, two keys, one file. Nothing else.

## 1. Anthropic API key (required)

Powers the actual pain-point extraction. Without this, the tool will not run at all.

1. Go to https://console.anthropic.com/settings/keys
2. Sign up / log in
3. Create a key, copy it

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
