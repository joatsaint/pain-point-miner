"""
fetch.py — turns a single YouTube URL into the transcript + comments .md
files indexer.py and pain_point_extractor.py already expect, with no other
project required. This is the missing first step: point this at a video,
then run indexer.py and pain_point_extractor.py on the result.

CLI:
    python -c "from fetch import fetch_video; fetch_video('https://youtube.com/watch?v=...')"

Optional: put a YOUTUBE_API_KEY in .env to also pull comments (free key at
https://console.cloud.google.com/apis/credentials, enable "YouTube Data API
v3"). Without it, comments are skipped and the transcript alone is fetched.
"""
import os
import re
from datetime import date
from urllib.parse import urlparse, parse_qs

import requests
from youtube_transcript_api import YouTubeTranscriptApi


def _load_env():
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

_load_env()


# ---------------------------------------------------------------------------
# URL / video ID
# ---------------------------------------------------------------------------

def extract_video_id(url):
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/").split("/")[0]
    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return qs["v"][0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/shorts/")[1].split("/")[0]
        if parsed.path.startswith("/live/"):
            return parsed.path.split("/live/")[1].split("/")[0]
    raise ValueError(f"Could not extract video ID from URL: {url}")


def _slugify(text, max_len=60):
    slug = text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    return slug[:max_len].rstrip('-')


# ---------------------------------------------------------------------------
# Metadata + transcript
# ---------------------------------------------------------------------------

def get_video_metadata(video_id):
    """Fetch title, channel name, and published date from the YouTube page."""
    metadata = {"title": video_id, "channel": "Unknown", "published": None}
    try:
        resp = requests.get(
            f"https://www.youtube.com/watch?v={video_id}",
            headers={"Accept-Language": "en-US,en;q=0.9"},
            timeout=10,
        )
        title_match = re.search(r'"title":"([^"]+)"', resp.text)
        if title_match:
            metadata["title"] = title_match.group(1)
        channel_match = re.search(r'"ownerChannelName":"([^"]+)"', resp.text)
        if channel_match:
            metadata["channel"] = channel_match.group(1)
        date_match = re.search(r'"publishDate":"([^"]+)"', resp.text)
        if date_match:
            metadata["published"] = date_match.group(1)[:10]
    except Exception:
        pass
    return metadata


def _clean_transcript(snippets):
    """Strip filler words, timestamps, and duplicate sentences (token efficiency)."""
    raw = " ".join(s.text for s in snippets)
    raw = re.sub(r'\[?\d{1,2}:\d{2}(?::\d{2})?\]?', '', raw)
    raw = re.sub(r'\bum+\b', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r'\buh+\b', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r',\s*like\s*,', ',', raw, flags=re.IGNORECASE)
    raw = re.sub(r',\s*you know\s*,', ',', raw, flags=re.IGNORECASE)
    raw = re.sub(r'\b(like|you know)\s*,', ',', raw, flags=re.IGNORECASE)
    raw = re.sub(r'\[(?:Music|Applause|Laughter|Music playing|Applauding|Cheering)\]', '', raw, flags=re.IGNORECASE)
    raw = re.sub(r' {2,}', ' ', raw)
    raw = raw.strip()

    sentences = re.split(r'(?<=[.!?])\s+', raw)
    deduped = []
    prev = None
    for s in sentences:
        s = s.strip()
        if s and s != prev:
            deduped.append(s)
        prev = s
    return ' '.join(deduped).strip()


def fetch_transcript_text(video_id):
    """Fetch and clean the transcript for a video. Raises on failure (no captions, etc.)."""
    api = YouTubeTranscriptApi()
    snippets = api.fetch(video_id, languages=["en"])
    return _clean_transcript(snippets)


# ---------------------------------------------------------------------------
# Comments (optional — needs YOUTUBE_API_KEY)
# ---------------------------------------------------------------------------

def fetch_comments(video_id):
    """
    Fetch top 100 comments by relevance via the YouTube Data API v3.
    Returns (comments_list, status) — never raises. status is one of:
    "ok" | "disabled" | "no_api_key" | "failed".
    """
    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        return [], "no_api_key"

    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/commentThreads",
            params={
                "part": "snippet",
                "videoId": video_id,
                "order": "relevance",
                "maxResults": 100,
                "textFormat": "plainText",
                "key": api_key,
            },
            timeout=10,
        )
        if not resp.ok:
            if resp.status_code == 403:
                return [], "failed"
            if resp.status_code == 400 and "commentsDisabled" in resp.text:
                return [], "disabled"
            return [], "failed"
        data = resp.json()
    except Exception:
        return [], "failed"

    comments = []
    for item in data.get("items", []):
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        comments.append({
            "author": snippet.get("authorDisplayName", "Unknown"),
            "text": snippet.get("textDisplay", ""),
            "like_count": snippet.get("likeCount", 0),
        })
    return comments, "ok"


# ---------------------------------------------------------------------------
# Write files in the format indexer.py / pain_point_extractor.py expect
# ---------------------------------------------------------------------------

def fetch_video(url, group="videos"):
    """
    Point this at a single YouTube URL. Writes:
      transcripts/<group>/<channel-slug>/<date>_<title-slug>.md
      transcripts/<group>/<channel-slug>/<date>_<title-slug>_comments.md  (if available)

    Returns the transcript file path.
    """
    video_id = extract_video_id(url)
    print(f"[fetch] Video ID: {video_id}")

    metadata = get_video_metadata(video_id)
    print(f"[fetch] \"{metadata['title']}\" — {metadata['channel']}")

    print("[fetch] Fetching transcript...", end=" ", flush=True)
    try:
        transcript = fetch_transcript_text(video_id)
    except Exception as exc:
        print("failed")
        print(f"[fetch] This video has no usable captions/transcript ({exc}). Try a different video.")
        return None
    print(f"ok ({len(transcript.split())} words)")

    channel_slug = _slugify(metadata["channel"]) or "unknown-channel"
    out_dir = os.path.join("transcripts", group, channel_slug)
    os.makedirs(out_dir, exist_ok=True)

    today = date.today().isoformat()
    title_slug = _slugify(metadata["title"])
    base_name = f"{today}_{title_slug}"
    transcript_path = os.path.join(out_dir, base_name + ".md")

    content = (
        f"# {metadata['title']}\n\n"
        f"**Channel:** {metadata['channel']}\n"
        f"**Published:** {metadata['published'] or 'Unknown'}\n"
        f"**URL:** {url}\n"
        f"**Downloaded:** {today}\n\n"
        f"---\n\n"
        f"## Transcript\n\n"
        f"{transcript}\n"
    )
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[fetch] Transcript saved: {transcript_path}")

    print("[fetch] Fetching comments...", end=" ", flush=True)
    comments, status = fetch_comments(video_id)
    if status == "no_api_key":
        print("skipped (no YOUTUBE_API_KEY in .env — transcript-only is fine, just fewer questions/pain points)")
    elif status == "disabled":
        print("skipped (comments disabled on this video)")
    elif status == "failed":
        print("failed (API error — continuing with transcript only)")
    else:
        comments_path = os.path.join(out_dir, base_name + "_comments.md")
        lines = [
            f"# Comments: {metadata['title']}",
            "",
            f"**Channel:** {metadata['channel']}",
            f"**Video URL:** {url}",
            f"**Comments Fetched:** {len(comments)}",
            "",
            "---",
            "",
            "## Top Comments (by relevance)",
            "",
        ]
        for c in comments:
            lines.append(c["text"])
            lines.append(f"— {c['author']} | {c['like_count']} likes")
            lines.append("")
            lines.append("---")
            lines.append("")
        with open(comments_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"ok ({len(comments)} comments) — saved: {comments_path}")

    print(f"\n[fetch] Done. Next: python -c \"from indexer import build_index; build_index(verbose=True)\"")
    return transcript_path
