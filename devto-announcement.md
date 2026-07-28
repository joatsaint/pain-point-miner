---
title: I built a free tool that reads a YouTube channel's transcripts and tells you what the audience actually wants
published: false
tags: python, ai, claudecode, opensource
canonical_url:
---

Twenty-five years in enterprise IT teaches you one thing whether you want it or not: how to sit in a room full of frustrated people and find the one real problem underneath all the noise. That's not a skill AI gave me. It's a skill I used for two decades on production incidents, just never had a name for outside of "reading the room."

So when I sat down to figure out what my own audience actually cares about, I didn't guess. I built something to tell me.

## The tool

[Pain Point Miner](https://github.com/joatsaint/pain-point-miner) — point it at a folder of YouTube transcripts and it hands back a ranked list of the questions, pain points, and outcomes that audience keeps bringing up. Two scripts, no framework, no dashboard:

- `indexer.py` scans the transcripts and builds a lightweight index
- `pain_point_extractor.py` runs each transcript through Claude, then aggregates everything into one report, ranked by how often each theme shows up

Real output from a three-video test run tonight:

```
## Top Pain Points (Most Expressed)
1. Existing business models built on inefficiencies closing on
   timelines measured in weeks, not decades — mentioned in 1 video(s)
```

## Why it's free

I'm not selling this. It's a free repo because the actual value isn't the code — four hundred lines of Python anyone could write in an afternoon — the value is knowing which question to ask the transcripts in the first place. That part came from the years, not the tool.

If you clone it, you bring your own Anthropic API key and pay Anthropic directly for your own usage. I don't see your data, I don't route your calls through anything of mine, and the whole thing costs a few cents to run against a handful of files.

## What it's for

Content creators who want to stop guessing what to make next. Small businesses trying to hear their own customers instead of assuming. Anyone staring at a pile of transcripts, comments, or reviews with no time to read all of it by hand.

Clone it, point it at your own channel, and see what your audience has been telling you the whole time.

Repo: [github.com/joatsaint/pain-point-miner](https://github.com/joatsaint/pain-point-miner)
