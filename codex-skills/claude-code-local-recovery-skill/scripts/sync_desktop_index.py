#!/usr/bin/env python3
import argparse
import glob
import json
import os
import re
import shutil
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def parse_ts(value):
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return int(datetime.fromisoformat(value).timestamp() * 1000)
    except Exception:
        return None


def text_from_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(x.get("text", "") for x in content if isinstance(x, dict) and x.get("type") == "text")
    return ""


def clean_title(value, fallback):
    value = re.sub(r"\s+", " ", value or "").strip()
    if not value:
        return fallback
    return value[:48].rstrip() + ("..." if len(value) > 48 else "")


def transcript_meta(path):
    cli_id = Path(path).stem
    cwd = origin_cwd = title = model = permission = first_user = None
    first_ms = last_ms = None
    completed_turns = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
            except Exception:
                continue
            ts = parse_ts(item.get("timestamp"))
            if ts is not None:
                first_ms = ts if first_ms is None else min(first_ms, ts)
                last_ms = ts if last_ms is None else max(last_ms, ts)
            cwd = cwd or item.get("cwd")
            origin_cwd = origin_cwd or item.get("originCwd") or item.get("cwd")
            if item.get("type") == "ai-title" and item.get("aiTitle"):
                title = item["aiTitle"]
            msg = item.get("message") or {}
            if isinstance(msg, dict):
                model = msg.get("model") or model
                if msg.get("role") == "assistant":
                    completed_turns += 1
                if msg.get("role") == "user" and first_user is None:
                    first_user = text_from_content(msg.get("content"))
            permission = permission or item.get("permissionMode")
    stat = os.stat(path)
    project_name = os.path.basename((cwd or "").rstrip("/")) or "Claude Code session"
    return {
        "cli_id": cli_id,
        "cwd": cwd,
        "origin_cwd": origin_cwd or cwd,
        "created_at": first_ms or int(stat.st_ctime * 1000),
        "last_at": max(last_ms or 0, int(stat.st_mtime * 1000)),
        "title": clean_title(title or first_user, project_name),
        "model": model or "claude-opus-4-8",
        "permission": permission or "auto",
        "completed_turns": completed_turns,
    }


def infer_current_index(base):
    data = load_json(Path.home() / ".claude.json") or {}
    acct = (data.get("oauthAccount") or {}).get("accountUuid")
    org = (data.get("oauthAccount") or {}).get("organizationUuid")
    if acct and org:
        return Path(base) / acct / org
    return None


def existing_cli_ids(index_dir):
    ids = set()
    names = set()
    for path in glob.glob(str(Path(index_dir) / "*.json")):
        names.add(Path(path).name)
        data = load_json(path)
        if data and data.get("cliSessionId"):
            ids.add(data["cliSessionId"])
    return ids, names


def index_json(meta, session_id):
    return {
        "sessionId": session_id,
        "cliSessionId": meta["cli_id"],
        "cwd": meta["cwd"],
        "originCwd": meta["origin_cwd"],
        "createdAt": meta["created_at"],
        "lastActivityAt": meta["last_at"],
        "model": meta["model"],
        "effort": "max",
        "isArchived": False,
        "title": meta["title"],
        "titleSource": "auto",
        "permissionMode": meta["permission"],
        "remoteMcpServersConfig": [],
        "completedTurns": meta["completed_turns"],
        "alwaysAllowedReasons": [],
        "sessionPermissionUpdates": [],
        "classifierSummaryEnabled": True,
        "spawnSeed": {},
    }


def main():
    parser = argparse.ArgumentParser(description="Sync Claude Desktop Code indexes from local raw transcripts.")
    parser.add_argument("--project-prefix", required=True, help="Only generate entries for transcripts under this cwd prefix.")
    parser.add_argument("--source-index-dir", help="Old account/org desktop index folder to copy from first.")
    parser.add_argument("--target-index-dir", help="New/current account/org desktop index folder. Defaults to ~/.claude.json oauth account.")
    parser.add_argument("--desktop-index-base", default=str(Path.home() / "Library/Application Support/Claude/claude-code-sessions"))
    parser.add_argument("--backup-dir", default="", help="Backup destination. Defaults beside target index base with timestamp.")
    parser.add_argument("--apply", action="store_true", help="Actually write changes. Without this, dry-run only.")
    parser.add_argument("--dry-run", action="store_true", help="Explicit dry-run.")
    args = parser.parse_args()

    target = Path(args.target_index_dir) if args.target_index_dir else infer_current_index(args.desktop_index_base)
    if not target:
        raise SystemExit("Could not infer target index; pass --target-index-dir.")

    prefix = args.project_prefix.rstrip("/")
    raw = []
    for path in glob.glob(str(Path.home() / ".claude/projects/**/*.jsonl"), recursive=True):
        try:
            meta = transcript_meta(path)
        except Exception:
            continue
        cwd = meta.get("cwd")
        if cwd and (cwd == prefix or cwd.startswith(prefix + "/")):
            raw.append(meta)

    existing_ids, existing_names = existing_cli_ids(target) if target.exists() else (set(), set())
    to_generate = [m for m in raw if m["cli_id"] not in existing_ids]
    source_files = glob.glob(str(Path(args.source_index_dir) / "*.json")) if args.source_index_dir else []
    source_to_copy = [p for p in source_files if Path(p).name not in existing_names]

    print("Claude Desktop Code Index Sync")
    print("=" * 31)
    print(f"Target: {target}")
    print(f"Project prefix: {prefix}")
    print(f"Raw transcripts under prefix: {len(raw)}")
    print(f"Existing target cli ids: {len(existing_ids)}")
    print(f"Source index files to copy: {len(source_to_copy)}")
    print(f"Generated entries needed: {len(to_generate)}")
    for cwd, count in Counter(m["cwd"] for m in to_generate).most_common(20):
        print(f"  {count:5d}  {cwd}")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to write changes.")
        return

    backup_dir = Path(args.backup_dir) if args.backup_dir else Path(args.desktop_index_base).parent / ("claude-code-sessions-backup-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    shutil.copytree(args.desktop_index_base, backup_dir, dirs_exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)

    copied = 0
    for src in source_to_copy:
        dst = target / Path(src).name
        if not dst.exists():
            shutil.copy2(src, dst)
            copied += 1

    existing_ids, existing_names = existing_cli_ids(target)
    generated = 0
    for meta in to_generate:
        if meta["cli_id"] in existing_ids:
            continue
        session_id = "local_" + meta["cli_id"]
        filename = session_id + ".json"
        if filename in existing_names:
            session_id = "local_" + str(uuid.uuid5(uuid.NAMESPACE_URL, meta["cli_id"] + (meta["cwd"] or "")))
            filename = session_id + ".json"
        with open(target / filename, "w", encoding="utf-8") as f:
            json.dump(index_json(meta, session_id), f, ensure_ascii=False, indent=2)
            f.write("\n")
        existing_ids.add(meta["cli_id"])
        existing_names.add(filename)
        generated += 1

    print(f"\nBackup: {backup_dir}")
    print(f"Copied source index files: {copied}")
    print(f"Generated new entries: {generated}")
    print("Restart Claude Desktop before checking Code mode.")


if __name__ == "__main__":
    main()
