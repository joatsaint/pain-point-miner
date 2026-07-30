# CLAUDE.md — Pain Point Miner entry point

Read this file completely before writing or running anything. This is the
first thing you (the AI) should act on when a user opens this project.

## Step 1 — Ask the user which mode they want. Do not assume, do not proceed without an answer.

Present these three options in your own words and wait for a reply:

**Option 1 — Fully Automatic**
Everything runs on its own: fetch the transcript, index it, extract the
pain points. Requires an Anthropic API key (see `SETUP.md`). This is the
free version — it processes one YouTube URL per run. (That limit isn't
enforced in code — it's just the intended scope of the free version. If a
user edits it to remove that, that's their call, not something to guard
against.)

**Option 2 — Manual / Zero-Cost**
No API key, no metered API calls, nothing installed beyond Python if they
want to run the scripts at all. The user copies a video's transcript (and
audience comments, if they want those included) themselves and pastes them
into one file, following the template in `manual-mode-template.md`, then
drops that file in `transcripts/<any-group>/<any-channel>/`. From there,
**you** (whichever AI they're talking to — Claude, Grok, ChatGPT, whatever
they have open, doesn't have to be Claude Code) read that file directly and
produce the same three-part analysis (Top Questions, Top Pain Points, Top
Desired Outcomes) right in the conversation. No need to run
`pain_point_extractor.py` at all for this option — the whole point is this
costs nothing beyond whatever AI access they already have.

**Option 3 — Builder Mode**
You do all the real work — write the code, run the scripts, everything —
but at the exact point where a file needs to physically move from one
place to another, you stop. Tell the user plainly: here's the file, here's
the exact folder path it goes in, let me know when it's there. Wait for
them to confirm, then continue. **This is deliberate, not a technical
limitation** — you could place the file yourself in most cases. The point
is to give the user one small, dead-simple, no-judgment-required hands-on
step, so they feel like they built something instead of just watching it
happen (the "add an egg" effect — see `BUILD_LOG.md` for the full framing
if you want the reasoning).

If they choose Option 3, ask one more question before starting: should the
**finished tool** end up fully automatic (Option 1's end state) or
semi-automatic (still requiring a manual file-drop each future run,
Option 2's end state)? Builder Mode is about how the BUILD is experienced
— pausing for hand-offs — not about what the finished tool looks like
once it's done. Both end states are valid; ask which one they want before
you start.

## Step 2 — proceed based on their answer

- **Option 1:** follow `SETUP.md` for the API key, then run the three
  commands in `README.md`'s "Run it" section.
- **Option 2:** point them to `manual-mode-template.md`, have them paste
  their transcript/comments into a file matching it, then read that file
  yourself and produce the analysis directly in the conversation. No script
  execution required.
- **Option 3:** build normally (same steps as Option 1 or the manual
  scripts, depending on which end state they picked), but pause at every
  physical file-move step per the protocol above.
