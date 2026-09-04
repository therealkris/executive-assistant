# Action Ledger

The durable state layer for action items. Shared by `action-review`, `morning-briefing`,
`eod-wrap`, and `weekly-review`.

Meeting notes, email, and chat are where action items **originate**. This ledger is where their
**status** lives. That split is the whole point: the meeting index is regenerated from the notes on
every ingest, so a completion recorded anywhere downstream of it is erased on the next rebuild. The
ledger is never regenerated — it is only appended to and amended.

**Check the capability first.** If `action-ledger` is not `enabled` in the config, or no ledger path
is set, skip every routine here and fall back to the pre-ledger behavior the calling skill declares.
**Who may create the ledger:** `setup`, during configuration; and `action-review`, when a user
invokes it interactively and agrees to create one. **A briefing never creates it** — a scheduled 7am
run must not quietly start writing state the user never asked for. It reports the gap and falls back.

---

## The file

One markdown file at the **Action ledger** path in `config.md`. Obsidian-readable, greppable,
hand-editable. Structure:

```markdown
# Action Items

Maintained by the executive-assistant plugin. Safe to edit by hand — keep the line shape and the IDs.

**Status:** `done` · `dropped` (decided against / no longer relevant) · `delegated` (someone else owns
the outcome now). Open items carry no status word; `waiting` marks one that is open but blocked on
someone else.

---

## Open

### acme

- [ ] `0de37e` Review current capacity and scale down now the launch has finished — org: acme · owner: Alex · source: [[2026-07-17 Launch capacity review]] · opened: 2026-07-17
- [ ] `922b34` Send the demo recording to Dana once the hardware arrives — org: acme · owner: Alex · source: [[2026-07-30 Dana–Alex]] · opened: 2026-07-30 · waiting: hardware arrival

### northwind

- [ ] `82081a` Communicate next steps to Jordan Ellis (decline) — org: northwind · owner: Alex · source: [[2026-07-29 Jordan Ellis Interview]] · opened: 2026-07-29 · due: 2026-08-05

## Closed

### northwind

- [x] `9e9334` Reschedule the network install — org: northwind · owner: Alex · source: [[2026-07-13 Sr Leadership]] · opened: 2026-07-13 · closed: 2026-08-03 · done · install landed 08-04
- [x] `d54e10` Verify what the new QA tool is and who needs it — org: northwind · owner: Alex · source: [[2026-07-29 Software Budget]] · opened: 2026-07-29 · closed: 2026-08-03 · dropped · card cancelled, closed by decision
```

Both `## Open` and `## Closed` are subdivided by `### <org>` — one level-3 heading per domain tag
in use, in the same order in both sections. The grouping is what makes a 90-item list readable and
what the skills' org-grouped display reads directly.

**Insert points matter.** Appending to the end of `## Open` puts an `acme` item under `### northwind`.
Always insert **under the matching `### <org>` heading**, creating it (alphabetically) if that org has
no items yet.

### Line grammar

```
- [ ] `<id>` <text> — <field>: <value> · <field>: <value> …
```

- **`<id>`** — six lowercase hex characters in backticks, optionally with a single-letter
  collision suffix. Stable and derived, never invented. See *Identity* below.
- **`<text>`** — the action, verbatim from the source where possible. One line. Strip any trailing
  `— owner: …` annotation from the source text; it becomes the `owner` field.
- **Fields**, separated by ` · `, in this order when present:

| Field | Required | Value |
|---|---|---|
| `org` | yes | one of the config's domain tags, without the `#` |
| `owner` | yes | the person accountable. The user's own name for their own items; someone else's name for a delegated item |
| `source` | yes | see *Source refs* |
| `opened` | yes | `YYYY-MM-DD` the item entered the ledger — **not** the date of the meeting that produced it, which the source link already carries |
| `due` | no | `YYYY-MM-DD`, only when the source states one |
| `waiting` | no | short reason the item is open but not actionable by the user |
| `bumped` | no | `YYYY-MM-DD` the user last consciously re-committed to a stale item. Resets the age clock; never overwrite `opened` |
| `closed` | closed only | `YYYY-MM-DD` |

  On a closed line, `closed:` is followed by the status word (`done` / `dropped` / `delegated`) and
  then, optionally, a short free-text outcome. Everything after the status word is prose — do not
  parse it.

### Source refs

| Origin | Form |
|---|---|
| Meeting note | `[[YYYY-MM-DD Title]]` — the Obsidian wikilink to the note, so it resolves in the vault. **If the filename contains `\|`, `[`, `]` or `#`, use a markdown link instead** — `[Title](<meetings folder>/YYYY-MM-DD Title.md)`. A title like `Dana \|\| Alex` inside `[[…]]` is parsed as a link plus an alias, so it silently resolves to nothing and a close-out write-back cannot find the note |
| Email | `email:<threadId>` |
| Chat | `chat:<permalink or channel/ts>` |
| Issue tracker | `tracker:<ISSUE-ID>` |
| Code review | `pr:<owner/repo#n>` |
| Said in conversation | `adhoc:YYYY-MM-DD` — the date it was captured |

Never leave `source` blank. An item with no traceable origin is the one that gets argued about later.

---

## Identity

The ID is a **derived fingerprint**, not a counter. This is what makes reconciliation idempotent:
re-scanning the same meeting note on a later run recomputes the same ID, finds it already in the
ledger, and adds nothing.

```
id = sha1( source_ref + "|" + normalized_text ).hexdigest()[:6]
```

`normalized_text` = the action text, lowercased, whitespace collapsed to single spaces, surrounding
markdown emphasis removed, trailing punctuation stripped, and any `— owner: …` / `(with X)` suffix
removed.

```bash
python3 -c "import hashlib,sys;print(hashlib.sha1(sys.argv[1].encode()).hexdigest()[:6])" \
  "[[2026-07-17 Launch capacity review]]|review current capacity and scale down now the launch has finished"
# -> 0de37e
```

**Collisions.** Six hex characters is 16.7M values — a collision inside a few hundred items is
possible but rare. If a computed ID already exists on a *different* item, append the next unused
lowercase letter (`0de37e` → `0de37ea`) and move on. Never reuse an ID across two different items.

**Edited source text.** If someone rewords an action item in its meeting note, the fingerprint
changes and naive reconciliation would add a duplicate. Before appending any new item, check the
ledger — **including the Closed section** — for an entry with the *same `source`* whose text shares
most of its significant words. On a strong match, update that entry's text in place and keep its
existing ID.

**The same commitment raised in two meetings.** This is the more common duplicate and the one that
breaks the promise that closed work stays closed. A recurring meeting produces a **new note per
occurrence**, so a standing commitment restated next week has a different `source`, a different
fingerprint, and sails past the same-source check — the user closes one copy and the other is still
open, and the following month mints a third.

So the near-match check runs **across sources too**: same `org`, high overlap of significant words,
regardless of `source`. A cross-source match is weaker evidence than a same-source one, so it is
never merged silently:

- Match against an **Open** entry → do not append. Add the new note's link to that entry's `source`
  field (space-separated) and keep the original ID.
- Match against a **Closed** entry → append the new item, and **tell the user in one line** that it
  looks like something they already closed on `<date>`, naming both IDs. A commitment genuinely
  raised again after being finished is real work; one that was merely restated in a recap is not,
  and only the user can tell those apart.

When the match is uncertain, add the item and flag it rather than merging.

---

## Reconcile

Run before displaying open items. Idempotent, safe to run repeatedly, and it never closes anything.

1. **Read the ledger.** Missing file → the capability is effectively absent; report it once and use
   the caller's fallback. Do not create the file mid-briefing.
2. **Collect candidates** for the caller's window:
   - Meeting notes — unchecked `- [ ]` lines under `## Action Items` where the owner is the user,
     unspecified, or shared, per `scan-sources.md`. Default window: **last 21 days**.
   - Anything the caller identified from email, chat, the tracker, or the conversation itself as a
     commitment the user has taken on.
3. **Compute the ID** for each candidate.
4. **Skip it when both the ID and the normalized text already appear in the ledger — Open or
   Closed.** The Closed half is the mechanism that stops a completed item from resurfacing; without
   it, every rebuild of the meeting index resurrects everything. Matching on the ID *alone* is the
   failure to avoid: on a fingerprint collision that silently discards the new item with no
   diagnostic, permanently. See *Collisions*.
5. **Near-match check** per *Edited source text* above.
6. **Append survivors** under their `### <org>` heading in `## Open`, with `opened:` set to
   **today** — the date the item entered the ledger, not the date of the meeting that produced it.
   The source wikilink already carries the meeting's date. This matters because the scan window and
   the stale threshold are both 21 days: back-dating `opened:` to the note's date would make an item
   captured from a three-week-old note *born stale*, and the weekly review would interrogate the
   user about neglecting something it had just shown them for the first time.
7. **Never delete, never reorder Closed, never rewrite `opened`.**

A ledger seeded during `setup` from an existing list is the one deliberate exception to step 6: those
items really have been open since their meeting dates, so back-dating `opened:` is accurate. Say so
in the file header when it applies.

Report reconciliation in one line — `3 new items tracked, 2 already known` — or say nothing if
nothing was added. It is plumbing, not news.

---

## Age and escalation

Age is `today − (bumped or opened)`.

| Age | Treatment |
|---|---|
| 0–6 days | Normal |
| 7–20 days | **Aging** — show the age in the overview |
| 21+ days | **Stale** — sort to the top, mark it, and ask about it explicitly |

**Nothing is ever auto-closed or auto-archived.** An item leaves the Open list only because the user
said so. When a stale item surfaces, ask directly whether it is done, dropped, or still real — and
if it is still real, record a `bumped:` date so the clock restarts and the file shows it was a
deliberate choice rather than neglect.

A `waiting:` item still ages. Blocked on someone else for three weeks is information, not an excuse
to hide it.

---

## Close

Triggered when the user says an item is finished, abandoned, or handed off. Free-form input — they
will say "the vendor renewal one is done", "first two are done, drop the third", or read out IDs.

1. **Resolve the reference to exactly one ID.** Match on ID first, then on distinctive words in the
   text, then on position in the list just shown. **If a reference resolves to more or fewer than
   one item, ask.** Never guess which item was meant, and never close an item on a partial match.
2. **Echo before writing.** List each ID, its text, and the status about to be recorded. This is the
   last cheap moment to catch a misheard reference.
3. **Move the line** from `## Open` to the top of `## Closed`: flip `- [ ]` to `- [x]`, append
   `· closed: <today> · <status>`, and add the user's own words as the outcome when they gave any.
4. **Write back to the origin note.** When `source` is a meeting-note wikilink, find the matching
   `- [ ]` line in that note and flip it to `- [x]`. If the line cannot be located unambiguously,
   say so in one line and continue — **the ledger is authoritative and the write-back is a
   courtesy**, so a failed write-back is never a reason to abandon the close.
5. **Confirm** with counts: `3 closed (2 done, 1 dropped) · 19 open`.

Rebuilding the meeting index after a write-back is optional and not worth doing for this alone; the
next ingest rebuilds it anyway, and the ledger does not depend on it.

---

## Reopen

Closing is the one destructive operation here — reconcile skips Closed IDs permanently, so an item
closed by mistake never comes back on its own. There must be a way out.

When the user says an item was closed in error, or that something they thought was finished is not:

1. Find it in `## Closed` by ID, or by text if they describe it.
2. Move the line back under its `### <org>` heading in `## Open`: flip `- [x]` to `- [ ]`, drop the
   `closed:` field and its status word and outcome, and set `bumped: <today>` so the age clock
   restarts from the reopen rather than from the original `opened:`.
3. If the origin note's checkbox was flipped on close, flip it back.
4. Confirm in one line.

Reopening is cheap and leaves a clean record. Never argue with the user about whether an item was
really finished — they are the only source of truth for that.

## Capture

New commitments that did not come from a scanned source — something the user says in passing, or a
follow-up the assistant proposed and they accepted.

Ask for nothing beyond the text. Infer `org` from context, set `owner` to the user's own name
unless they name someone else, `source: adhoc:<today>`, `opened: <today>`. Add a `due:` only if they state one — an
invented deadline is worse than none.

**Do not capture speculatively.** A suggestion in a briefing is not a commitment. Something becomes
an action item when the user accepts it, not when the assistant proposes it.
