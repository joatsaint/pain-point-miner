# Build Your Own Pain Point Miner — 3-Phase Prompt

Paste these into Claude Code (or any AI coding agent) one at a time, in order.
Each phase should work and be testable before you move to the next — don't
skip ahead if a phase isn't actually running yet.

You don't need any of my code to use this. This is the method, not the repo.
If you just want the working tool, grab the repo instead — link below.

---

## Phase 1 — The Indexer

```
I want to build a tool that reads a folder of YouTube transcript files
(plain markdown, one file per video) and builds a searchable index of
what's in them.

Folder structure:
transcripts/<group-name>/<channel-name>/<video-title>.md

Each .md file has a plain text header with at least a video title and
channel name, followed by the transcript body.

Build a single Python script, indexer.py, with one function:
build_index(verbose=False) that:
1. Walks the transcripts/ folder recursively
2. Parses each .md file's header for title, channel, and group (inferred
   from the folder path)
3. Writes a single JSON index file (knowledge_base/index.json) listing
   every transcript found, with its file path, title, channel, and group
4. Is safe to re-run any time — it's a full rebuild from scratch every time,
   never incremental, since the transcripts are the source of truth

No external dependencies — standard library only. Print a one-line summary
when done: how many transcripts, channels, and groups were indexed.
```

Test it: drop 2-3 real transcript `.md` files into a `transcripts/<group>/<channel>/`
folder and run it. You should get a real `index.json` back. Don't move to
Phase 2 until this works.

---

## Phase 2 — The Extractor (Pass 1)

```
Now build pain_point_extractor.py. It reads the index.json from Phase 1,
and for each transcript in a given group, sends the transcript text to
Claude (use Haiku — this needs to be cheap, it's running per-file) with a
prompt asking it to return ONLY a JSON object with three arrays:

{
  "questions": ["direct question the speaker or audience asks/implies"],
  "pain_points": ["frustration, problem, or complaint expressed"],
  "desired_outcomes": ["what the speaker/audience explicitly wants instead"]
}

Write one function: run_extractor(group="group-name") that:
1. Loads the index, filters to that group
2. For each transcript, calls Claude, parses the JSON response
3. Handles a failed/malformed JSON response by logging it and skipping —
   never crash the whole run over one bad file
4. Saves each file's raw extraction as its own small JSON file so Pass 2
   doesn't need to re-call Claude

Use max_tokens generous enough that longer transcripts don't get cut off
mid-JSON (a truncated response is a common failure mode here — don't
under-budget this).
```

Test it on the same 2-3 files. Read the raw per-file JSON output and sanity
check it against what's actually in the transcript.

---

## Phase 3 — The Aggregator (Pass 2)

```
Add a second pass to pain_point_extractor.py's run_extractor(): after all
per-file extractions are done, aggregate them into one ranked report.

Group near-duplicate questions/pain points/outcomes together (an LLM call
or simple text-similarity grouping both work), count how many distinct
videos mention each theme, and rank each of the three categories by that
count, most-mentioned first.

Write the final result as a single markdown report:
knowledge_base/reports/pain_points_<date>_<group>.md

with three ranked sections: Top Questions, Top Pain Points, Top Desired
Outcomes — each entry showing the theme and "mentioned in N video(s)".

Print a one-line run summary: how many files processed, how many API
calls made, rough token count.
```

Test it end to end on your own real transcripts. This is the whole tool —
two scripts, no framework, no dashboard.

---

## What you get from this that you don't get from cloning the repo

Cloning gets you my code. Running these three prompts gets you the exercise
of directing an AI through a real build, one testable phase at a time —
which is the actual transferable skill. The code is disposable. Knowing how
to ask for it isn't.

Repo: [github.com/joatsaint/pain-point-miner](https://github.com/joatsaint/pain-point-miner)
