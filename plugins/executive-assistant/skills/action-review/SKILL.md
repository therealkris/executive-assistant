---
name: action-review
description: Shows what action items are still open across meetings, email, chat, and conversation, then records what the user says is finished so it stops resurfacing. Use when the user asks "what's still open", "what's on my list", "what do I owe people", "mark that done", "that's finished", "drop that item", "close out my action items", or when a briefing hands off to an action-item review.
---

# Action Review

Show what is still open, take the user's word on what is finished, and write it down so it does not
come back. Direct and concise — this is a working pass, not a report.

## Capabilities

**Required:** `action-ledger`

- Absent → say plainly that action-item tracking is not set up, and **offer to create the ledger
  now** — it is one file with two headings, and this skill is interactive, so there is no reason to
  bounce the user to `setup` for it. On a yes, create it per `action-ledger.md`, record the path and
  `action-ledger: enabled` in the config, then reconcile and continue normally. On a no, stop.
- Do not improvise a list from meeting notes instead: a list with no state is exactly the problem
  this skill exists to fix.

**Optional:** `meeting-notes`, `mail`, `chat`, `issue-tracker`

Each optional capability only widens what reconciliation can pull in. All absent → the ledger still
works, holding whatever was captured by hand or by another skill.

## Load first

- `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` — **read this first.** Where the config lives and
  how to degrade. Then read the config for the ledger path, domain tags, and workspace paths.
- `${CLAUDE_PLUGIN_ROOT}/shared/action-ledger.md` — the ledger format, ID scheme, and the
  **Reconcile**, **Close**, and **Capture** routines. Everything below assumes it.
- `${CLAUDE_PLUGIN_ROOT}/shared/scan-sources.md` — only if reconciling from meeting notes.

---

## Which mode

The user's opening message decides. Do not run all three.

| They said | Mode |
|---|---|
| "what's open", "what's on my list", "where do things stand" | **Overview** |
| "X is done", "close those two", "drop that one" | **Close** — and if no list was shown this session, show one first so the reference resolves against something visible |
| "add a task", "remind me to", "put this on my list" | **Capture** |
| "that wasn't done", "reopen that", "I closed that by mistake" | **Reopen** — per `action-ledger.md` |
| Anything mixed | Overview, then Close, then Capture — in that order |

## Overview

1. **Reconcile** per `action-ledger.md`. Default window 21 days for meeting notes. Report new items
   in one line, or say nothing if there were none.
2. **Group by org** using the config's domain tags. Within each org, order: **stale first**, then by
   due date, then by age.
3. Per item, one line: the ID, the text, and — only when they exist — the due date, the age if
   aging or stale, the `waiting:` reason, and the source. Nothing else. No commentary paragraphs, no
   restating the same item three ways.
4. **Lead with the stale block** if there is one, under its own heading, because those are the items
   the user has stopped seeing.
5. Close with the counts: `21 open · 4 stale · 2 due this week`.

Then ask, once:

> Anything here done, dropped, or handed off? Give me the IDs or just describe them.

Ask it once and stop. Do not walk the list item by item unless the user asks for that.

## Close

Follow the **Close** routine in `action-ledger.md` exactly — resolve to exactly one ID, echo before
writing, move the line, write back to the origin meeting note, confirm with counts.

Two rules worth restating because they are where this goes wrong:

- **An ambiguous reference is a question, not a guess.** "The vendor renewal thing" matching two items
  means asking which, not picking the likelier one. A wrongly closed item disappears silently and the
  user finds out weeks later.
- **A failed write-back to a meeting note is not a failed close.** Report it in one line and move on.

If the user closes a **stale** item's neighbours but says nothing about the stale item itself, ask
about that one specifically before finishing. It is the whole reason it was sorted to the top.

## Reopen

Follow the **Reopen** routine in `action-ledger.md`. Never push back on whether the item was really
finished — the user is the only source of truth for that.

## Capture

Follow the **Capture** routine in `action-ledger.md`. Confirm in one line with the new ID, so the
user has something to reference later.

## Standalone runs

When invoked directly rather than from a briefing, keep the whole exchange short: reconcile, show,
ask, write, confirm. No email delivery, no summary of what the ledger is for, no restating the
counts twice. The user asked what is open — answer that.
