#!/usr/bin/env python3
"""Rebuild meetings/INDEX.md and meetings/.index/meetings.db from the markdown notes.

The markdown notes are the source of truth; both indexes are disposable and fully
regenerated on every run. Safe to run anytime:  python3 build_index.py [meetings_dir]
"""
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

M = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_note(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        return None
    fm_text, _, body = text[3:].partition("\n---")
    note = {"path": os.path.basename(path), "body": body.strip()}

    def field(name):
        m = re.search(rf"^{name}: (.+)$", fm_text, re.M)
        return m.group(1).strip().strip('"') if m else ""

    note["title"] = field("title")
    note["date"] = field("date")
    note["time"] = field("time")
    note["status"] = field("status") or "complete"
    note["source_id"] = field("source_id")
    note["source_doc"] = field("source_doc")
    note["transcript"] = field("transcript")
    def list_field(name):
        """Read a frontmatter list in either form:

            name: [a, b]          # inline
            name:                 # block
              - a
              - b

        Scoping matters: an unscoped '- item' regex over the whole frontmatter
        pulls every block list into whichever field asked first, so a block
        'entities:' would silently land in 'attendees'.
        """
        inline = field(name)
        if inline:
            return [v.strip().strip('"') for v in inline.strip("[]").split(",") if v.strip()]
        m = re.search(rf"^{name}:[ \t]*\n((?:[ \t]+-[ \t]*.+\n?)+)", fm_text, re.M)
        if not m:
            return []
        return [
            v.strip().strip('"')
            for v in re.findall(r"^[ \t]+-[ \t]*(.+?)[ \t]*$", m.group(1), re.M)
            if v.strip()
        ]

    note["jobs"] = [j.strip() for j in field("job").strip("[]").split(",") if j.strip()]
    note["entities"] = list_field("entities")
    note["attendees"] = []
    for raw in list_field("attendees"):
        em = re.search(r"<([^>]+)>", raw)
        note["attendees"].append({
            "name": re.sub(r"<[^>]*>", "", raw).strip(),
            "email": em.group(1).strip() if em else "",
        })

    # sections
    sections = {}
    for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", body, re.M | re.S):
        sections[m.group(1).strip().lower()] = m.group(2).strip()
    note["summary"] = sections.get("summary", "")
    note["decisions"] = [
        re.sub(r"\*\*", "", d.strip())
        for d in re.findall(r"^- (.+?)(?=^- |\Z)", sections.get("decisions", ""), re.M | re.S)
    ]
    note["actions"] = []
    for m in re.finditer(r"^- \[( |x)\] (.+)$", sections.get("action items", ""), re.M):
        item = m.group(2).strip()
        owner = ""
        om = re.search(r"[—-]\s*owners?: ([^—\n]+)", item)
        if om:
            owner = om.group(1).strip()
        note["actions"].append({"text": item, "owner": owner, "done": m.group(1) == "x"})
    return note


def one_liner(note, limit=170):
    s = " ".join(note["summary"].split())
    if not s:
        return "(empty — nothing captured)" if note["status"] == "empty" else ""
    cut = s.find(". ")
    s = s[: cut + 1] if 0 < cut < limit else s
    return s[: limit - 1] + "…" if len(s) > limit else s


def short_attendees(note, n=4):
    names = [a["name"].split()[0] for a in note["attendees"] if a["name"]]
    return ", ".join(names[:n]) + (f" +{len(names)-n}" if len(names) > n else "")


def build(meetings_dir):
    notes = []
    for f in sorted(os.listdir(meetings_dir)):
        if f.endswith(".md") and f != "INDEX.md":
            n = parse_note(os.path.join(meetings_dir, f))
            if n:
                notes.append(n)
    notes.sort(key=lambda n: (n["date"], n["time"]), reverse=True)

    # --- INDEX.md ---
    rows = ["# Meetings Index", "", f"_{len(notes)} meetings · rebuilt {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by .scripts/build_index.py_", "",
            "| Date | Note | Job | Attendees | Summary |", "|------|------|-----|-----------|---------|"]
    for n in notes:
        link = f"[[{n['path'][:-3]}]]"
        summary = one_liner(n).replace("|", "/")
        rows.append(f"| {n['date']} | {link} | {', '.join(n['jobs'])} | {short_attendees(n)} | {summary} |")
    with open(os.path.join(meetings_dir, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")

    # --- SQLite ---
    idx_dir = os.path.join(meetings_dir, ".index")
    os.makedirs(idx_dir, exist_ok=True)
    db_path = os.path.join(idx_dir, "meetings.db")
    # Build in a local temp dir first: SQLite locking fails on some mounted/synced
    # filesystems (iCloud, sandbox mounts). The finished file is then copied over.
    import shutil
    import tempfile
    tmp_db = os.path.join(tempfile.mkdtemp(), "meetings.db")
    db = sqlite3.connect(tmp_db)
    db.executescript("""
    CREATE TABLE meetings(source_id TEXT PRIMARY KEY, title TEXT, date TEXT, time TEXT,
        status TEXT, jobs TEXT, path TEXT, transcript TEXT, source_doc TEXT, summary TEXT);
    CREATE TABLE attendees(source_id TEXT, name TEXT, email TEXT);
    CREATE TABLE entities(source_id TEXT, entity TEXT);
    CREATE TABLE decisions(source_id TEXT, text TEXT);
    CREATE TABLE actions(source_id TEXT, text TEXT, owner TEXT, done INTEGER);
    CREATE VIRTUAL TABLE notes_fts USING fts5(source_id UNINDEXED, title, body);
    CREATE VIRTUAL TABLE transcripts_fts USING fts5(source_id UNINDEXED, body);
    """)
    for n in notes:
        db.execute("INSERT INTO meetings VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (n["source_id"], n["title"], n["date"], n["time"], n["status"],
                    ",".join(n["jobs"]), n["path"], n["transcript"], n["source_doc"], one_liner(n, 400)))
        db.executemany("INSERT INTO attendees VALUES(?,?,?)",
                       [(n["source_id"], a["name"], a["email"]) for a in n["attendees"]])
        db.executemany("INSERT INTO entities VALUES(?,?)", [(n["source_id"], e) for e in n["entities"]])
        db.executemany("INSERT INTO decisions VALUES(?,?)", [(n["source_id"], d) for d in n["decisions"]])
        db.executemany("INSERT INTO actions VALUES(?,?,?,?)",
                       [(n["source_id"], a["text"], a["owner"], int(a["done"])) for a in n["actions"]])
        db.execute("INSERT INTO notes_fts VALUES(?,?,?)", (n["source_id"], n["title"], n["body"]))

    tdir = os.path.join(meetings_dir, "transcripts")
    t_count = 0
    if os.path.isdir(tdir):
        for f in sorted(os.listdir(tdir)):
            if not f.endswith(".md"):
                continue
            text = open(os.path.join(tdir, f), encoding="utf-8").read()
            sid = re.search(r"^source_id: (\S+)", text, re.M)
            db.execute("INSERT INTO transcripts_fts VALUES(?,?)", (sid.group(1) if sid else f, text))
            t_count += 1
    db.commit()
    counts = {t: db.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ["meetings", "attendees", "entities", "decisions", "actions"]}
    db.close()
    # copyfile overwrites in place (no unlink) — deletion is restricted on some mounts
    shutil.copyfile(tmp_db, db_path)
    print(f"INDEX.md: {len(notes)} rows | meetings.db: {counts} | transcripts indexed: {t_count}")


if __name__ == "__main__":
    build(M)
