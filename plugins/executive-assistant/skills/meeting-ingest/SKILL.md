---
name: meeting-ingest
description: Incremental ingest of completed meeting notes from a document source (e.g. Google Drive AI meeting notes) and Notion into a local meetings/ knowledge base, with a completion gate so in-progress meetings are never captured. Use when the user says "ingest my meetings", "pull my meeting notes", "sync my meeting notes", "process my meeting transcripts", "catch up the meeting repo", or when the scheduled ingest run fires.
---

# Meeting Ingest

Incremental ingest of completed meeting notes from **two sources** — a document source (AI-generated
meeting notes in cloud storage) and Notion — into the local meetings knowledge base.

On a frequent cadence **most runs will find nothing new; that is expected.** Be fast and quiet: if
nothing is new, do almost nothing and report one line.

## Capabilities

**Required:** `meeting-ingest-source`

- Absent → do not run. Say that no meeting-note source is configured and that `setup` can add one.
- Configured with only one of the two sources → run that source and don't mention the other.
  The config names which sources exist; a missing upstream ingest skill means document-source ingest
  is simply skipped, and Notion-only ingest is a valid setup.

## Load first

- `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` — **read this first.** Where the config lives and
  how to degrade. Then read the config for paths, accounts, job tag, upstream ingest skill, and
  transcription corrections.

Output locations all come from the config's path table: notes in the meeting-notes folder,
transcripts in the transcripts folder, state in the ingest state file, index alongside it.
Apply the config's capitalization rules in all prose and entity tags.

---

## Critical rule — only ingest COMPLETED meetings

**Never ingest a meeting that may still be in progress or still being finalized.** A meeting being
recorded right now must not be captured until it has clearly ended and its notes have settled.
Apply the gate to both sources.

**Notion completion gate.** A Notion meeting note is "completed" only if **both** hold:

1. Its `last_edited_time` is at least **30 minutes** in the past, computed against the current time
   at run. While a meeting records, Notion streams the transcript and updates the page continuously,
   so `last_edited_time` stays fresh — a 30-minute quiet period means the recording ended and the AI
   summary settled.
2. The page body contains a generated summary / notes section, **not just raw streaming
   transcript.** A page that is only an unstructured wall of transcript with no summary block is
   still being processed.

If either is false, **skip the note this run and do not mark it processed** — it will qualify on a
later run once it goes quiet.

**Document-source completion gate.** Most AI note-takers publish only after the meeting ends, so
these are inherently complete. Still apply the same 30-minute quiet check using the document's
modified time as a guard.

## Source 1 — Document source

If the config names an **upstream ingest skill**, run it with the Skill tool and follow its
instructions exactly — it owns the document-source workflow, note schema, account sanity check,
dedupe ledger, and transcript archiving. Notes:

- Use the **job tag** from the config.
- The expected document-source account is in the config; the upstream skill's account sanity check
  must pass. **If the connector serves a different account, STOP and report. Do not ingest.**
- Incremental, **not** backfill: honor `last_run` with the upstream skill's overlap window (typically
  7 days) and the processed ledger / cross-job `source_id` checks.
- Enforce the 30-minute quiet gate above before distilling any document.

If the config names no upstream skill, skip this source and ingest from Notion only.

## Source 2 — Notion

Use the Notion connector's meeting-notes query tool. Filterable properties are typically limited to
title, attendees, `created_time`, `created_by`, `last_edited_time`, `last_edited_by` — there is **no
status field**, so completion must be inferred via the gate above.

1. **Query candidates.** Filter `last_edited_time` on-or-after an exact datetime ~7 days before now
   (overlap slack), in the user's timezone. Returns notes where the user is attendee or creator.
2. **Dedupe.** Read the ingest state file. Maintain a `processed_notion` map (Notion page ID → note
   path) alongside the document-source `processed` map. Skip any page ID already in
   `processed_notion`. Also grep the notes folder for `source_id: <notion-page-id>`.
3. **Completion gate.** Fetch each surviving candidate and apply both conditions above. Skip —
   without marking processed — anything that fails.
4. **Cross-source dedupe (best effort).** The same meeting may also be captured by the document
   source. Before writing, grep the notes folder for an existing note with the same date and
   overlapping attendees/topic. If a strong match exists, do **not** write a second note — append
   `notion` to the existing note's `source` and record the Notion page ID in `processed_notion`
   pointing at that note. When unsure, write the Notion note but add a Context line flagging a
   possible duplicate of that day's other note.
5. **Distill** each completed, new Notion note into `YYYY-MM-DD <Topic>.md` using the **same template
   the upstream skill uses** — frontmatter (title, job, date, time, attendees, entities, source_doc,
   source_id, transcript, status, tags), then Summary / Decisions / Action Items / Open Questions /
   Key Quotes / Context. Mapping:
   - date/time from the note's date (title mention-date or `created_time`) in the user's timezone
   - `<Topic>` a real topic from the title or summary; if the title is generic like "Meeting," infer a
     concise topic from content
   - `source_doc` = Notion page URL; `source_id` = Notion page ID; add `source: notion` to frontmatter
   - if the page has a verbatim transcript section, archive it to
     `<transcripts folder>/YYYY-MM-DD <Topic> (transcript).md` (minimal frontmatter, verbatim) and
     link it; otherwise leave the recording link
   - apply the config's **transcription corrections** to distilled prose;
     **preserve verbatim inside Key Quotes**
6. **Empty notes.** If a completed Notion note genuinely has no content, write a minimal note with
   `status: empty` and mark it processed.

## State and index

- Update the ingest state file. The upstream skill maintains `last_run` and `processed`; you
  additionally maintain `processed_notion`. Add each newly ingested Notion page ID.
- **If anything changed** from either source, rebuild the derived indexes via bash:

  ```
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_index.py" <meetings dir>
  ```

  The script is **bundled with this plugin** — it is not something the user supplies. It regenerates
  `INDEX.md` and the SQLite + FTS5 database from the notes, building in a temp directory and copying
  into place so it survives cloud-synced and network mounts. Markdown notes are the source of truth;
  both indexes are disposable and can be deleted and rebuilt at any time.

  If `python3` is unavailable, prepend the `INDEX.md` row manually and note that the SQLite index
  could not be rebuilt. Downstream skills fall back to reading notes directly, so this degrades
  rather than breaks.

### Frontmatter format — write lists exactly this way

The index parser reads `attendees` and `entities` from frontmatter. Write **one item per line**, and
put the email in angle brackets:

```yaml
attendees:
  - Alex Chen <alex@example.com>
  - Dana Reed
entities:
  - Example Corp
```

Put any annotation **after** the email, not between the name and it — `Alex Chen <alex@example.com>
(invited, did not attend)` parses correctly. Quote a value only if YAML requires it; surrounding
quotes are stripped.

Both inline (`entities: [A, B]`) and block form parse correctly, and each list is scoped to its own
key, so a block-form `entities` will not leak into `attendees`. Stay consistent anyway — mixed forms
across notes make the vault harder to read and diff.

## Report

One short block: documents/notes found per source, how many new, how many skipped as incomplete
(still in progress / not yet settled), how many skipped via dedupe, how many empty, and the list of
new note titles. Confirm the index rebuild counts. If zero new across both sources, say so in one
line.
