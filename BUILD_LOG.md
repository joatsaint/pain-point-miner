# Pain Point Miner — Build Log

Running log of the actual build, kept for the end-of-video project scope
recap. Entries in order, real decisions only — not a marketing narrative.

---

## 2026-07-27 — Origin & scope decision

Spun out of the youtube-downloader project's existing pain-point-extraction
pipeline (`src/knowledge_base/indexer.py` + `src/analyzer/pain_point_extractor.py`).
Decision: pull out just the extraction piece, not the rest of the pipeline
(no downloading, no channel registry, no Reddit) — Simplest-Path-First call,
made explicit after Randy asked how much of the existing project needed to
come along.

- Copied `indexer.py` verbatim (zero changes).
- Copied `pain_point_extractor.py` with exactly one edit: the import path
  (`from src.knowledge_base.indexer import load_index` →
  `from indexer import load_index`).
- Proved the standalone version works end to end: real index built (3
  transcripts, 1 channel, 1 group), extraction run against real transcripts
  (2/3 succeeded, 1 hit the pre-existing JSON-truncation bug, documented
  honestly rather than hidden).

## 2026-07-27 — Content assets drafted

- `README.md` — full setup/run instructions, real sample output, an honest
  "here's a real bug it caught" section instead of pretending it's flawless.
- `devto-announcement.md` — announcement-style article (not a build-log
  style piece), per Randy's explicit direction.
- External prior-art check run before finalizing positioning: real
  competitors found (PainScout, PainPoints.fast, generic AI pain-point
  generators). Differentiation locked as free/open-source/self-run vs. their
  paid/closed SaaS — not "no one else does this."

## 2026-07-28 — Build-it-yourself prompt series

`build-it-yourself-prompts.md` — a 3-phase prompt sequence (indexer →
pass-1 extractor → pass-2 aggregator) that lets someone rebuild the same
tool with their own AI, instead of only offering the repo. Decision: offer
both the repo (fast path) and the prompts (the teaching path) as two
separate CTAs in the video, not one or the other.

## 2026-07-28 — Public-repo-readiness audit (pre-push)

Ran a privacy/copyright audit before creating the GitHub repo. One real
finding, HIGH priority: the three sample transcript files used for local
testing are full, verbatim copies of real "AI News & Strategy Daily |
Nate B Jones" YouTube videos — someone else's copyrighted spoken content,
not Randy's own. Decision: exclude `transcripts/`, the built
`knowledge_base/index.json`, and `logs/` from the public repo entirely
(gitignored, kept locally only). The one generated report
(`pain_points_2026-07-27_ai-and-claude-code.md`) stays as the public sample
output — it's Randy's own transformative analysis, not a reproduction of
the source video.

---

*(Next entries: repo creation, first push, live URL, CTA link verification.)*
