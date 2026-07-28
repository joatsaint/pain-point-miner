"""
Pain Point Extractor — Phase 3 core business intelligence module.

Two-pass approach:
  Pass 1: One Claude API call per transcript/comment file pair → structured JSON
  Pass 2: One aggregation call → master ranked list with mention counts

Output: knowledge_base/reports/pain_points_YYYY-MM-DD_[group].md
Log:    logs/analyzer_log.json
"""
import json
import os
import time
from datetime import datetime, timezone

import anthropic

from indexer import load_index


ANALYZER_LOG = "logs/analyzer_log.json"
REPORTS_DIR = "knowledge_base/reports"


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


def _read_file(path, max_chars=6000):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_chars)
    except Exception:
        return ""


def _pass1_extract(client, model, transcript_chunk, comments_chunk):
    """
    Extract questions, pain points, desired outcomes from one file pair.
    Returns parsed dict or None on failure.
    """
    content = f"""Analyze this content and return JSON with exactly this structure:
{{
  "questions": ["question 1", "question 2", "question 3", "question 4", "question 5"],
  "pain_points": ["pain 1", "pain 2", "pain 3", "pain 4", "pain 5"],
  "desired_outcomes": ["outcome 1", "outcome 2", "outcome 3"]
}}

TRANSCRIPT CONTENT:
{transcript_chunk}

COMMENT CONTENT (weight 2x):
{comments_chunk}"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=500,
            system="You are a market research analyst. Extract pain points and questions from content. Return ONLY valid JSON. No prose. No markdown.",
            messages=[{"role": "user", "content": content}],
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text), response.usage.input_tokens + response.usage.output_tokens
    except Exception as e:
        print(f"[WARN] Pass 1 extraction failed: {e}")
        return None, 0


def _pass2_aggregate(client, model, all_extractions, videos_analyzed):
    """
    Aggregate all per-file extractions into a master ranked list.
    Returns parsed dict or None on failure.
    """
    content = f"""Aggregate these per-video extractions into a master ranked list.
Count how many videos mention each theme. Merge similar items.
Return JSON with exactly this structure:
{{
  "top_questions": [
    {{"text": "question text", "count": 5, "category": "getting started"}},
    {{"text": "question text", "count": 3, "category": "tools"}}
  ],
  "top_pain_points": [
    {{"text": "pain point", "count": 8, "category": "technical"}},
    {{"text": "pain point", "count": 4, "category": "mindset"}}
  ],
  "top_desired_outcomes": [
    {{"text": "outcome", "count": 6, "category": "career"}},
    {{"text": "outcome", "count": 3, "category": "skills"}}
  ],
  "videos_analyzed": {videos_analyzed},
  "total_extractions": {len(all_extractions)}
}}

DATA:
{json.dumps(all_extractions)}"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            system="You are a market research analyst. Aggregate and rank pain point data. Return ONLY valid JSON. No prose.",
            messages=[{"role": "user", "content": content}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text), response.usage.input_tokens + response.usage.output_tokens
    except Exception as e:
        print(f"[ERROR] Pass 2 aggregation failed: {e}")
        return None, 0


def _render_report(aggregated, group_name, files_processed, comment_files_count, today):
    """Render the final Markdown report."""
    display_name = group_name.replace("-", " ").title()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# Pain Point Analysis: {display_name}",
        f"**Generated:** {now}",
        f"**Videos Analyzed:** {files_processed}",
        f"**Comment Files Included:** {comment_files_count}",
        f"**Group:** {group_name}",
        "",
        "---",
        "",
        "## Top Questions (Most Asked)",
        "",
    ]

    for i, item in enumerate(aggregated.get("top_questions", []), 1):
        lines.append(f"{i}. {item['text']} — mentioned in {item['count']} video(s)")
    lines.append("")

    lines += ["## Top Pain Points (Most Expressed)", ""]
    for i, item in enumerate(aggregated.get("top_pain_points", []), 1):
        lines.append(f"{i}. {item['text']} — mentioned in {item['count']} video(s)")
    lines.append("")

    lines += ["## Top Desired Outcomes (What They Want)", ""]
    for i, item in enumerate(aggregated.get("top_desired_outcomes", []), 1):
        lines.append(f"{i}. {item['text']} — mentioned in {item['count']} video(s)")
    lines.append("")

    # PDF product opportunities — derive from top questions
    lines += ["---", "", "## PDF Product Opportunities", ""]
    lines.append("Based on the above, the highest-priority PDF topics are:")
    lines.append("")
    top_qs = aggregated.get("top_questions", [])
    for i, item in enumerate(top_qs[:3], 1):
        demand = "HIGH" if item["count"] >= 5 else "MEDIUM" if item["count"] >= 3 else "LOW"
        lines.append(f"{i}. **{item['text']}**")
        lines.append(f"   Estimated demand: {demand}")
        lines.append("")

    lines += [
        "---",
        f"*Generated by YouTube Transcript Downloader Pain Point Extractor*",
        f"*Source: {files_processed} transcripts + {comment_files_count} comment files from {group_name} category*",
    ]

    return "\n".join(lines)


def _append_analyzer_log(run_id, group, files_processed, api_calls, tokens_used, output_file):
    os.makedirs("logs", exist_ok=True)
    log = {"runs": []}
    if os.path.exists(ANALYZER_LOG):
        try:
            with open(ANALYZER_LOG, "r", encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            pass

    # Estimate cost: Haiku ~$0.80/M input + $4/M output tokens (rough avg $1/M)
    estimated_cost = round(tokens_used / 1_000_000 * 1.0, 6)

    log["runs"].append({
        "run_id": run_id,
        "group": group,
        "files_processed": files_processed,
        "api_calls_made": api_calls,
        "tokens_used": tokens_used,
        "estimated_cost_usd": estimated_cost,
        "output_file": output_file,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    with open(ANALYZER_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def run_extractor(group=None):
    """
    Run pain point extraction for one group or all groups.

    Args:
        group: Group folder name (e.g. 'ai-and-claude-code'), or None for all groups.
    """
    model = os.getenv("ANALYZER_MODEL", "claude-haiku-4-5-20251001")
    max_files = int(os.getenv("ANALYZER_MAX_FILES", "50"))

    client = anthropic.Anthropic()
    index = load_index()

    groups_to_process = []
    for group_name, group_data in index.get("groups", {}).items():
        if group and group_name != group:
            continue
        # Flatten channels → transcripts into the entry format expected by _run_for_group
        files = []
        for channel_data in group_data.get("channels", {}).values():
            for entry in channel_data.get("transcripts", []):
                file_path = entry["file_path"]
                comments_path = (
                    file_path.replace(".md", "_comments.md")
                    if entry.get("has_comments")
                    else None
                )
                files.append({
                    "path": file_path,
                    "filename": os.path.basename(file_path),
                    "comments_path": comments_path,
                })
        if files:
            groups_to_process.append((group_name, files))

    if not groups_to_process:
        target = f"group '{group}'" if group else "any group"
        print(f"[ANALYZE] No transcript files found for {target}. Run 'index' first.")
        return

    for group_name, files in groups_to_process:
        _run_for_group(client, model, max_files, group_name, files)


def _run_for_group(client, model, max_files, group_name, files):
    run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    today = datetime.now().strftime("%Y-%m-%d")

    files = files[:max_files]
    print(f"\n[ANALYZE] Group: {group_name} — {len(files)} file(s) to process")

    all_extractions = []
    api_calls = 0
    total_tokens = 0
    comment_files_count = 0

    # Pass 1 — per-file extraction
    for i, entry in enumerate(files, 1):
        transcript_path = entry.get("path", "")
        comments_path = entry.get("comments_path")

        transcript_chunk = _read_file(transcript_path, max_chars=60_000)  # covers a full ~1-hour transcript
        comments_chunk = _read_file(comments_path, max_chars=8_000) if comments_path else ""

        if comments_chunk:
            comment_files_count += 1

        print(f"  [{i}/{len(files)}] {entry.get('filename', '')} ...", end=" ", flush=True)

        result, tokens = _pass1_extract(client, model, transcript_chunk, comments_chunk)
        api_calls += 1
        total_tokens += tokens

        if result:
            result["source_file"] = entry.get("filename", "")
            all_extractions.append(result)
            print("ok")
        else:
            print("skipped")

        # Brief pause to avoid rate limiting
        if i < len(files):
            time.sleep(0.5)

    if not all_extractions:
        print(f"[ANALYZE] No extractions succeeded for group '{group_name}'.")
        return

    # Pass 2 — aggregation
    print(f"\n[ANALYZE] Aggregating {len(all_extractions)} extraction(s)...")
    aggregated, tokens = _pass2_aggregate(client, model, all_extractions, len(files))
    api_calls += 1
    total_tokens += tokens

    if not aggregated:
        print("[ANALYZE] Aggregation failed — check logs.")
        return

    # Save report
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_filename = f"pain_points_{today}_{group_name}.md"
    report_path = os.path.join(REPORTS_DIR, report_filename)

    report_content = _render_report(
        aggregated, group_name, len(files), comment_files_count, today
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"[ANALYZE] Report saved: {report_path}")
    print(f"[ANALYZE] API calls: {api_calls} | Tokens: {total_tokens:,}")

    _append_analyzer_log(run_id, group_name, len(files), api_calls, total_tokens, report_path)
