#!/usr/bin/env python3
import argparse
import glob
import json
import os
from collections import Counter
from pathlib import Path


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def read_transcript_meta(path):
    meta = {"path": path, "cli_id": Path(path).stem, "cwd": None, "title": None}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                meta["cwd"] = meta["cwd"] or item.get("cwd")
                if item.get("type") == "ai-title" and item.get("aiTitle"):
                    meta["title"] = item["aiTitle"]
                if meta["cwd"] and meta["title"]:
                    break
    except Exception:
        pass
    return meta


def index_entries(index_dir):
    ids = set()
    files = []
    for path in glob.glob(str(Path(index_dir) / "*.json")):
        data = load_json(path)
        if not data:
            continue
        files.append(data)
        if data.get("cliSessionId"):
            ids.add(data["cliSessionId"])
    return ids, files


def main():
    parser = argparse.ArgumentParser(description="Audit local Claude Code recovery state.")
    parser.add_argument("--project-prefix", default="", help="Only count raw transcripts whose cwd starts with this path.")
    parser.add_argument("--desktop-index-base", default=str(Path.home() / "Library/Application Support/Claude/claude-code-sessions"))
    args = parser.parse_args()

    claude_json = load_json(Path.home() / ".claude.json") or {}
    account = claude_json.get("oauthAccount") or {}
    current_account = account.get("accountUuid")
    current_org = account.get("organizationUuid")
    current_index = None
    if current_account and current_org:
        current_index = Path(args.desktop_index_base) / current_account / current_org

    raw_paths = glob.glob(str(Path.home() / ".claude/projects/**/*.jsonl"), recursive=True)
    metas = [read_transcript_meta(p) for p in raw_paths]
    if args.project_prefix:
        prefix = args.project_prefix.rstrip("/")
        metas = [m for m in metas if m.get("cwd") and (m["cwd"] == prefix or m["cwd"].startswith(prefix + "/"))]

    raw_by_cwd = Counter(m.get("cwd") or "(unknown)" for m in metas)

    print("Claude Code Local Recovery Audit")
    print("=" * 39)
    print(f"Current account: {current_account or '(unknown)'}")
    print(f"Current org:     {current_org or '(unknown)'}")
    print(f"Current index:   {current_index or '(not inferred)'}")
    print(f"Raw transcripts: {len(metas)}")
    print()
    print("Raw transcripts by cwd:")
    for cwd, count in raw_by_cwd.most_common(30):
        print(f"  {count:5d}  {cwd}")

    print()
    print("Desktop index folders:")
    base = Path(args.desktop_index_base)
    for folder in sorted(base.glob("*/*")):
        if not folder.is_dir():
            continue
        ids, files = index_entries(folder)
        cwd_counts = Counter(f.get("cwd") or "(unknown)" for f in files)
        mark = "  < current" if current_index and folder == current_index else ""
        print(f"  {len(files):5d} files, {len(ids):5d} cli ids  {folder}{mark}")
        for cwd, count in cwd_counts.most_common(5):
            print(f"         {count:5d}  {cwd}")

    if current_index and current_index.exists():
        current_ids, _ = index_entries(current_index)
        missing = [m for m in metas if m["cli_id"] not in current_ids]
        print()
        print(f"Missing from current desktop index: {len(missing)}")
        for cwd, count in Counter(m.get("cwd") for m in missing).most_common(20):
            print(f"  {count:5d}  {cwd}")


if __name__ == "__main__":
    main()
