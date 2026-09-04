---
name: relationship-cms
description: Builds and refreshes the user's people/ relationship CRM by scanning email, chat, and the meetings index over a trailing 30 days, counting touchpoints, writing profiles, and optionally mirroring entries into memory. Use when the user asks to update their contacts or CRM, refresh people profiles, "who have I been talking to", or when the scheduled run fires.
---

# Relationship CRM

Maintain the user's relationship CRM — markdown profiles of the people they interact with regularly,
used to feed daily briefings and meeting preps with context.

**Run fully; do not ask questions** — on scheduled runs no one is watching.

## Capabilities

**Required:** at least one of `mail`, `chat`, `meeting-notes`
**Optional:** `outbound-email`, `memory-mirror`

- **All three required sources absent** → do not run; there are no touchpoints to count.
- Any individual source absent → skip it and say which sources were live in the report. Touchpoint
  counts are only meaningful relative to the sources actually scanned, so the 3+ threshold for adding
  a new profile applies to whatever was available.
- `people-crm` path not configured → do not run; there is nowhere to write profiles. Point at `setup`.
- `memory-mirror` absent → skip step 5 entirely and say the mirror was skipped. This is the default.
- `outbound-email` absent → **only** when no tool can send mail at all. Prefer a dedicated
  automation sender; otherwise send with the mail connector from the user's own account. See
  `email-delivery.md` for the ordering. Genuinely absent → deliver the report in chat.

## Load first

- `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` — **read this first.** Where the config lives and
  how to degrade. Then read the config for accounts, org domains, paths, and name normalizations.
- `${CLAUDE_PLUGIN_ROOT}/shared/scan-sources.md` — mail, chat, and meetings-index conventions
- The people CRM folder's `_TEMPLATE.md` (profile template) and `_README.md` (schema/rules) —
  **read both before writing anything.** If they don't exist, create a reasonable template and README
  first and say so in the report.

---

## Step 1 — Gather 30 days of signal

Trailing 30 days from today. Run all three independently.

**a) Email.** Search **inbox only** across the user's work accounts and domains listed in
`config.md`, for the last 30 days. Collect each correspondent's name + email and a one-line
thread-topic summary. Do not surface archived mail.

**b) Chat.** Find DMs and channel messages the user participated in over the last 30 days. Map
handles and display names to real people. Capture topic summaries.

**c) Meetings.** Per the meetings-index method in `scan-sources.md` — copy the DB to a temp path
first, then query meetings in the window:

```python
python3 - <<'PY'
import sqlite3, shutil, tempfile, os
src = "<meeting index path>"
tmp = os.path.join(tempfile.mkdtemp(), "m.db")
shutil.copy(src, tmp)
db = sqlite3.connect(tmp)
for row in db.execute(
    "SELECT date, title FROM meetings "
    "WHERE date >= date('now','-30 day') ORDER BY date DESC"
):
    print(row)
PY
```

Use the Python module, not the `sqlite3` CLI — the CLI isn't installed in every environment. See
`scan-sources.md`.

Pull attendees, decisions, and actions per meeting. Use the documented fallbacks (rebuild the index,
then read notes directly) if the DB is missing, empty, or returns nothing.

## Step 2 — Count touchpoints per person

A **touchpoint** = one email thread, one chat DM/thread, or one meeting in the window. Tally per
person across all sources.

Apply the **name normalizations** in `config.md` so one person doesn't become two. Ignore automated
and no-reply senders, mailing lists, and the user themselves.

## Step 3 — Decide who to write

- **REFRESH** every existing profile already in the people folder (files not prefixed with `_`),
  regardless of touchpoint count.
- **ADD** a new profile only for a person not yet in the folder with **3+ touchpoints** in the window.
- Skip `_TEMPLATE.md` and `_README.md`.

## Step 4 — Write / update profiles

**New profile:** copy the `_TEMPLATE.md` structure. Filename `first-last.md`, kebab-case;
disambiguate collisions by org (e.g. two people named Alex Chen become `alex-chen-acme.md` and
`alex-chen-globex.md`). Fill frontmatter — emails, aliases including chat handle, org, relationship,
cadence, `last_interaction`, sources, created, updated — and the body.

**Existing profile: AUGMENT, do not overwrite.**

- Append newest-first bullets to `## Recent Interactions`, formatted
  `- YYYY-MM-DD — [email|chat|meeting] short summary`. Keep roughly the last 10. Do not duplicate
  dates already logged.
- Update `## Open Threads / Commitments` with anything outstanding.
- Update frontmatter `last_interaction`, `sources`, `updated`.
- **Never alter hand-written sections** like "How to Work With Them" / "User Manual."

Use the file tools the config designates for local files.

## Step 5 — Mirror to memory (only if the config sanctions it)

Check the **Memory writes** convention in `config.md`. Scheduled runs must not write to auto-memory
unless the config explicitly names this skill as a sanctioned exception. **If it doesn't, skip this
step entirely** and note the skip in the report.

If sanctioned: for each person profiled this run, create or update a concise memory entry
(`type: reference`) capturing who they are, their relationship to the user, primary email, current
cadence, and any live open thread. Keep the memory index in sync — one line per person. **Update
existing entries rather than duplicating.** Flag any contradiction with what was previously stored —
in your report — before overwriting.

## Step 6 — Report

Email a summary per `${CLAUDE_PLUGIN_ROOT}/shared/email-delivery.md`:

| Field | Value |
|---|---|
| SUBJECT | `Weekly Relationship CRM — <date>` |
| Body | profiles refreshed (count + names); new profiles added (names + why); notable new open threads/commitments surfaced; which sources were live vs. unavailable; whether the memory mirror ran or was skipped; any contradictions flagged |

Plain text is sufficient for this report — the full HTML spec is optional here. Keep it tight,
direct, no fluff. Cite the source channel for each interaction logged.
