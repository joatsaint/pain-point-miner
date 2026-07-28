"""
Knowledge base indexer.

Scans all .md transcript files in transcripts/, extracts metadata from each
file header, and builds knowledge_base/index.json — the lookup table for
query.py and digest.py.

Always rebuilds from scratch. Index is derived data; transcripts are the
source of truth. Running twice is always safe.

CLI (via main.py):
    python -m src.main index
    python -m src.main index --group bitcoin-macro
    python -m src.main index --verbose
"""
import json
import os
import re
import sys
from datetime import datetime, timezone


TRANSCRIPTS_ROOT = "transcripts"
KB_DIR = "knowledge_base"
INDEX_PATH = os.path.join(KB_DIR, "index.json")

_VIDEO_ID_PATTERNS = [
    re.compile(r'[?&]v=([A-Za-z0-9_-]{11})'),
    re.compile(r'youtu\.be/([A-Za-z0-9_-]{11})'),
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_metadata(path):
    """
    Read the header block of a transcript .md file and return a dict:
        title, channel, date, video_id

    Raises ValueError if title or channel are missing (malformed file).
    """
    title = channel = published = url = ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("# ") and not title:
                    title = line[2:].strip()
                elif line.startswith("**Channel:**") and not channel:
                    channel = line.replace("**Channel:**", "").strip()
                elif line.startswith("**Published:**") and not published:
                    published = line.replace("**Published:**", "").strip()
                elif line.startswith("**URL:**") and not url:
                    url = line.replace("**URL:**", "").strip()
                # Stop at the separator — no need to read transcript body
                if line == "---" and title and channel:
                    break
    except OSError as exc:
        raise ValueError(f"Cannot read file: {exc}") from exc

    if not title:
        raise ValueError("missing title (# heading)")
    if not channel:
        raise ValueError("missing **Channel:** field")

    video_id = ""
    for pattern in _VIDEO_ID_PATTERNS:
        m = pattern.search(url)
        if m:
            video_id = m.group(1)
            break

    return {"title": title, "channel": channel, "date": published, "video_id": video_id}


def _word_count(path):
    """Count words in the transcript body (text after the first --- separator)."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        if "---" in content:
            content = content.split("---", 1)[-1]
        return len(content.split())
    except OSError:
        return 0


def _write_index_atomic(index):
    """
    Write index.json via a temp file + atomic rename so a Ctrl-C mid-write
    never leaves a partial file.
    """
    os.makedirs(KB_DIR, exist_ok=True)
    tmp_path = INDEX_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(index, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_path, INDEX_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_index(group_filter=None, verbose=False):
    """
    Scan transcripts/ and write knowledge_base/index.json.

    Args:
        group_filter: If provided, only index this group name (str).
        verbose:      If True, print each file as it is indexed.

    Returns the completed index dict.
    Calls sys.exit(1) on fatal errors (missing transcripts/ dir, write failure).
    """
    # Step 1 — validate transcripts/ exists
    if not os.path.isdir(TRANSCRIPTS_ROOT):
        print(
            "transcripts/ directory not found. "
            "Run a channel download first."
        )
        sys.exit(1)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    index = {
        "built_at": now,
        "total_transcripts": 0,
        "groups": {},
    }

    total = 0
    warnings = 0

    # Step 2 — iterate group folders
    try:
        group_entries = sorted(os.listdir(TRANSCRIPTS_ROOT))
    except OSError as exc:
        print(f"Cannot read transcripts/ directory: {exc}")
        sys.exit(1)

    for group_name in group_entries:
        group_path = os.path.join(TRANSCRIPTS_ROOT, group_name)
        if not os.path.isdir(group_path):
            continue
        if group_filter and group_name != group_filter:
            continue

        channels_data = {}

        # Walk recursively to handle both flat (group/file.md) and
        # nested (group/channel-name/file.md) directory layouts.
        for dirpath, dirnames, filenames in os.walk(group_path):
            dirnames.sort()

            # Channel from directory structure when possible.
            # rel == "." means we are directly inside the group folder (flat layout).
            rel = os.path.relpath(dirpath, group_path)
            dir_channel = None if rel == "." else rel.split(os.sep)[0]

            # Step 2 cont — exclude _comments.md from the main index
            md_files = sorted(
                f for f in filenames
                if f.endswith(".md") and not f.endswith("_comments.md")
            )

            for filename in md_files:
                filepath = os.path.join(dirpath, filename)
                rel_filepath = filepath.replace("\\", "/")

                # Step 3 — extract metadata from file header
                try:
                    meta = _extract_metadata(filepath)
                except ValueError as exc:
                    print(f"[INDEX] WARNING: skipping {rel_filepath} — {exc}")
                    warnings += 1
                    continue

                # Channel: prefer directory name; fall back to header value
                channel_name = dir_channel or meta["channel"]

                # Step 4 — check for companion _comments.md
                base = filename[:-3]
                has_comments = os.path.isfile(
                    os.path.join(dirpath, base + "_comments.md")
                )

                # Step 5 — word count of transcript body
                wc = _word_count(filepath)

                entry = {
                    "file_path": rel_filepath,
                    "video_id": meta["video_id"],
                    "title": meta["title"],
                    "channel": channel_name,
                    "group": group_name,
                    "date": meta["date"],
                    "has_comments": has_comments,
                    "word_count": wc,
                }

                if verbose:
                    print(f"  [+] {group_name}/{channel_name}/{filename}")

                # Step 6 — accumulate into group/channel structure
                if channel_name not in channels_data:
                    channels_data[channel_name] = {"total": 0, "transcripts": []}
                channels_data[channel_name]["transcripts"].append(entry)
                channels_data[channel_name]["total"] += 1
                total += 1

        group_total = sum(ch["total"] for ch in channels_data.values())
        index["groups"][group_name] = {
            "total": group_total,
            "channels": channels_data,
        }

    index["total_transcripts"] = total

    # Step 7 — atomic write
    try:
        _write_index_atomic(index)
    except Exception as exc:
        print(f"[INDEX] ERROR: failed to write index.json — {exc}")
        if os.path.exists(INDEX_PATH):
            try:
                os.remove(INDEX_PATH)
            except OSError:
                pass
        sys.exit(1)

    # Step 8 — terminal confirmation
    group_count = len(index["groups"])
    channel_count = sum(len(g["channels"]) for g in index["groups"].values())
    warn_note = f" ({warnings} file(s) skipped with warnings)" if warnings else ""
    print(
        f"Index built: {total} transcript(s) across "
        f"{channel_count} channel(s) in {group_count} group(s).{warn_note}"
    )

    return index


def load_index():
    """Load the existing index from disk, building it first if missing."""
    if not os.path.exists(INDEX_PATH):
        return build_index()
    with open(INDEX_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)
