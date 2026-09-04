# Source Scan Conventions

How to read each source. Shared by `morning-briefing`, `eod-wrap`, `weekly-review`,
`meeting-prep`, and `relationship-cms`.

Accounts, paths, channels, and org names come from the config. This file describes **method**, not
values — if you need a specific address or channel name, it's in the config.

**Check the capability first.** Each section below corresponds to a capability in
`capabilities.md`. If the config marks it anything other than `enabled`, or the relevant config
section is missing or empty, **skip that source** — don't attempt the read, don't report an error,
and don't substitute a guess. The calling skill collects the skips and reports them in one closing
line.

---

## Mail

**Every query must be scoped to the inbox** (in Gmail syntax, `in:inbox`). This is non-negotiable
and enforced at the query level — never filter after the fact. Archived mail is considered already
actioned and must never surface.

Noise reduction, where useful: `-in:sent -category:promotions -category:social`

For each message surfaced, give sender, subject, timestamp, and a one-line summary.
If an account returns nothing, **say so explicitly per account** — do not silently omit it. A
missing account and an empty account look identical in the output otherwise.

Thread reads: request full thread content with analysis enabled where the connector supports it
(e.g. `get_gmail_thread_content` with `include_analysis=true`). Check the last sender and whose
court the ball is in to determine whether the user already responded.

## Chat / Slack

Scan the channels and DMs listed in `config.md`.

Surface **only** items that need a reply or action from the user — direct questions, @-mentions,
requests, decisions awaiting them, or threads where they were the last expected responder and
haven't replied. Skip FYIs, resolved threads, and anything already answered.

Per flagged item: source (DM with [name], or channel name), who, a one-line summary, and why it
needs them. If a source has nothing, say "no items needing attention" — do not pad.
Zero search results means **"no relevant messages found"**, never "not connected."

## Issue tracker

Examples below use Linear's tool names; adapt to your tracker.

1. Resolve the current user (`get_user` "me").
2. List issues assigned to them, plus the filter the calling skill needs.

**Due-today view** (morning): issues assigned to the user due today. Flag overdue issues separately.
Do not list issues without due dates. If nothing qualifies, say "no issues due today."

Per issue: issue ID and title; status, priority, due date; project/team if set.

**Activity view** (end of day): add `updatedAt: <today>`, `orderBy: updatedAt`. Group into:

- **Completed today** — status type `completed` **and** the completion timestamp is today. Do not
  count issues completed on an earlier date that were merely touched today.
- **Moved** — workflow state changed today (e.g. now "Ready for Review", "In Progress")
- **Updated** — still-open issues touched today with no completion

Per issue: identifier, title, current status, priority — one line each. Note coherent blocks of work
(several issues from one project/epic closed together) in a single sentence rather than padding.

**Verification caveat:** filtering by assignee + last-updated is a proxy — it does not prove the user
was the actor of every change. A completion timestamp of today plus assignment to them is strong
evidence of completion. For issues merely "updated," do not assert which field changed unless
evidence is available. Disclose this limitation briefly, only if it matters.

If nothing was touched, say "no tracker activity today" and move on.

## Meeting notes

Notes in the meeting-notes folder are the **source of truth**. Any SQLite index is a disposable
derivative.

**Query the index first.** Two constraints:

1. **Copy the DB to a writable temp path before querying.** SQLite locking fails on network and
   cloud-synced mounts.
2. **Use Python's `sqlite3` module, not the `sqlite3` CLI.** The command-line tool is frequently
   absent — it isn't present in the Cowork sandbox, for instance — while the Python module is part of
   the standard library and always available.

```python
python3 - <<'PY'
import sqlite3, shutil, tempfile, os
src = "<meeting index path>"
tmp = os.path.join(tempfile.mkdtemp(), "m.db")
shutil.copy(src, tmp)
db = sqlite3.connect(tmp)
for row in db.execute("SELECT date, title FROM meetings ORDER BY date DESC LIMIT 10"):
    print(row)
PY
```

If you reach for the `sqlite3` CLI and get "command not found", that is the expected condition, not a
broken install — switch to the form above rather than concluding the index is unavailable.

Schema:

- `meetings(source_id, title, date, time, status, jobs, path, transcript, source_doc, summary)`
- `attendees(source_id, name, email)`
- `entities(source_id, entity)`
- `decisions(source_id, text)`
- `actions(source_id, text, owner, done)`
- `notes_fts(source_id, title, body)` — FTS5, search with `MATCH`
- `transcripts_fts(source_id, body)` — FTS5, search with `MATCH`

Then read the matching note(s) for nuance once the query narrows the set.
For verbatim quotes, search `transcripts_fts`, then read the file in the transcripts folder.

**Fallbacks**, in order, if the DB is missing, 0 bytes, or returns nothing:

1. Rebuild it with the index script named in `config.md`, then retry.
2. Read notes directly from the notes folder, selecting files whose `YYYY-MM-DD` filename prefix
   falls in the window. Parse attendees / decisions / action items from frontmatter and body.

**Open action items:** lines under an `## Action Items` heading that are unchecked (`- [ ]`) where
the user is the owner, or the owner is unspecified or shared. Skip anything checked `- [x]`.

**Caveat:** the `done` column reflects ingest-time state, not reality. Treat action items as a triage
list, not a live tracker. The `jobs` column separates one org's context from another's.

## Web search

Only for external facts. Every item must come from a real, dated source found via search at run
time — never from training knowledge. Cite source name and link. Skip anything undated or outside
the requested window.
