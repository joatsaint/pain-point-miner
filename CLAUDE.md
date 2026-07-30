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
You run the existing, already-working scripts (`fetch.py`, `indexer.py`,
`pain_point_extractor.py`) yourself, step by step, the same way Option 1
or Option 2 would — you are NOT re-deriving the code from scratch live
(that's a different, separate thing: `build-it-yourself-prompts.md`, for
a user who explicitly wants the 3-phase "write it yourself" exercise
instead of this). Builder Mode's job is to make the existing build feel
hands-on, not to reinvent it.

If they choose Option 3, first ask: should the **finished tool** end up
fully automatic (Option 1's end state) or semi-automatic (Option 2's end
state, still requiring a manual transcript-paste each future run)? This
decides WHERE your one pause point is — there is exactly one real manual
step in this system depending on which end state they pick, and that's
where you stop:

- **If they picked fully automatic:** the one unavoidable manual step is
  creating the `.env` file with their Anthropic API key (see `SETUP.md`).
  Do everything else yourself, then stop right there: tell them plainly
  to create `.env` in this folder with their key, and let you know when
  it's done. Wait for confirmation, then run the tool for real and show
  them the report.
- **If they picked semi-automatic:** the one manual step is the
  transcript-paste-and-save from `manual-mode-template.md`. Set everything
  else up, then stop there: tell them to paste their transcript into the
  template and save it at the exact path, and let you know when it's
  done. Wait for confirmation, then read that file and produce the
  analysis yourself.

Don't invent an additional pause beyond that one real step — this system
genuinely only has one hands-on moment per end state. The point isn't to
manufacture busywork, it's to make sure the one real manual step in the
process is framed as *their* contribution, not something to script around
(the "add an egg" effect — see `BUILD_LOG.md` for the full framing).

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
