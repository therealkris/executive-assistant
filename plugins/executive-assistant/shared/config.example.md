# Configuration — template

**You probably don't need to edit this by hand. Run the `setup` skill instead** — it detects which
tools you have connected, asks a few multiple-choice questions, and writes your config for you.

This file is the reference for what setup produces. Your filled-in copy lives **outside the plugin
directory**, because that directory is replaced on every plugin update and anything stored there is
silently discarded. Setup picks whichever of these your environment can reach:

- `~/.claude/plugins/data/<plugin-id>/config.md` — in Claude Code (terminal)
- `<your connected folder>/.executive-assistant/config.md` — in the Cowork desktop app, which can
  only reach folders you've explicitly connected

See `capabilities.md` for the full resolution order.

Every skill reads your config. Nothing else in the plugin should hardcode a personal value.

**Delete any section you don't need.** A skill whose section is missing skips that work and says so —
that's a supported outcome, not a failure. See `capabilities.md` for exactly how each skill degrades.

---

## Capabilities

The switchboard. Skills read this to know what they can use. `enabled` means the tool is connected
and configured; **anything else means the skill skips that work rather than guessing or failing.**

Setup fills this in from what it detects. Keep a row for every capability even when it's off — it
makes the file self-documenting.

| Capability | Status | Notes |
|---|---|---|
| `mail` | `enabled` / `not configured` | Reading the inbox |
| `mail-draft` | `enabled` / `not configured` | Creating in-thread reply drafts. Separate from `mail` — reading doesn't imply drafting |
| `calendar` | `enabled` / `not configured` | |
| `chat` | `enabled` / `not configured` | Slack, Teams, etc. |
| `issue-tracker` | `enabled` / `not configured` | |
| `meeting-notes` | `enabled` / `not configured` | Reading the local notes base |
| `meeting-ingest-source` | `enabled` / `not configured` | Writing new notes from a document source or Notion |
| `outbound-email` | `enabled` / `not configured` | Satisfied by any send-capable tool — a dedicated automation sender, or the mail connector's own send. `not configured` only when nothing can send mail; then briefings go to chat |
| `web-search` | `enabled` / `not configured` | Absent → the Updates digest is omitted |
| `expense-tool` | `enabled` / `not configured` | |
| `voice-profile` | `enabled` / `not configured` | Absent → drafts use a neutral tone |
| `people-crm` | `enabled` / `not configured` | |
| `daily-logs` | `enabled` / `not configured` | |
| `action-ledger` | `enabled` / `not configured` | Durable action-item state. Absent → completions aren't remembered and items resurface |
| `memory-mirror` | `enabled` / `not configured` | Permission to mirror contacts into memory. **Default off** |

---

## Identity

- **Name:** `<full name>` — goes by `<preferred name>`
- **Pronouns:** `<optional, e.g. he/him — used when skills write about you in the third person>`
- **Roles:**
  - `<title>` at `<primary organization>` — `<one line on what the org does>`
  - `<title>` at `<secondary organization, if any>` — `<one line, plus any end date if this role is winding down>`
  - `<any other entity you own or advise>`
- **Key colleagues:** `<name>` — `<role, e.g. CEO / co-founder>`; add as many as briefings need
- **Communication style:** `<how you want output written, e.g. direct and concise, no fluff, no speculation, disclose uncertainty explicitly, cite sources>`

## Organizations

List every org you're affiliated with. Skills use this to tell **internal** from **external**
people, which drives whether an attendee gets a web-research pass in `meeting-prep`.

| Organization | Email domain(s) | Notes |
|---|---|---|
| `<primary org>` | `<domain.com>` | primary — default context when ambiguous |
| `<subsidiary or second org>` | `<domain.com>` | |
| `<day job / other employer>` | `<domain.com>` | |
| `<holding or back-office entity>` | `<domain.com>` | |

Anyone whose email domain is **not** on this list is external.

## Accounts

| Purpose | Value |
|---|---|
| Primary work | `<you@primary-org.com>` |
| Secondary work | `<you@second-org.com>` |
| Personal | `<you@personal.com>` |
| Day job | `<you@employer.com>` |
| Outbound automation sender | `<inbox-id@agentmail.to>` — **optional.** A dedicated address briefings are sent *from*, so they stay out of your Sent folder. Leave blank to send from your primary work account instead |
| Briefing recipient | `<you@primary-org.com>` — where briefings are delivered |
| Expense intake | `<receipts@expensify.com or your expense tool's intake address>` |

**Which accounts each skill touches:** by default, briefings scan every account listed above and
inbox triage operates **only** on Primary work. If you want different scoping, say so here
explicitly — e.g. "inbox triage: primary work only; briefings: primary + personal."

## Connector rules

Adjust to match your setup. These are the non-obvious ones worth writing down:

- **Reads and labeling:** `<which connector, e.g. the Google Workspace connector>`
- **Drafting:** `<which connector, and any required parameters>`. If your setup splits reads from
  drafts, note it — some connectors create standalone drafts instead of in-thread replies, which
  breaks reply threading. Whichever tool you use must accept a thread ID and an in-reply-to message
  ID.
- **Calendar:** `<which connector>`
- **Local files:** `<preferred tools, e.g. direct file tools rather than an MCP wrapper>`
- **Outbound mail:** `<connector name, or leave blank>`. If no dedicated sender is named, briefings are
  sent with the mail connector's own send tool from your primary work account. If the send tool isn't
  loaded, find it via tool search before assuming it's unavailable.

## Workspace paths

Root: `<absolute path to your notes/workspace root>`

If your shell or sandbox mounts this root at a different path, note the mapping here — skills that
run bash need it.

| What | Path (relative to root) |
|---|---|
| Voice profile | `<e.g. Voice Profile.md>` |
| People / relationship CRM | `<e.g. memory/people/>` |
| Daily logs | `<e.g. Daily Logs/>` |
| Action ledger | `<e.g. Action Items.md>` — durable; **never delete or regenerate this one** |
| Meeting notes | `<e.g. meetings/>` |
| Meeting transcripts | `<e.g. meetings/transcripts/>` |
| Meeting index (SQLite) | `<e.g. meetings/.index/meetings.db>` — generated; safe to delete and rebuild |
| Meeting ingest state | `<e.g. meetings/.state/ingest.json>` |
| Index rebuild script | `${CLAUDE_PLUGIN_ROOT}/scripts/build_index.py` — **bundled with the plugin; leave as-is** |
| Workspace instructions | `<e.g. CLAUDE.md, MEMORY.md>` |

## Chat / Slack scope

Channels to scan: `<#channel>`, `<#channel>`, `<#channel>`, plus all direct messages.

If a chat search returns zero results, report **"no relevant messages found"** — never
"not connected." An empty result and a broken connector are different problems, and conflating them
hides real outages.

## Calendar attribution

If you hold more than one role, recurring meetings get misattributed. List the ambiguous ones:

| Meeting title | Belongs to |
|---|---|
| `<recurring meeting name>` | `<org>` |
| `<recurring meeting name>` | `<org>` |

Rules:

- `<any heuristic, e.g. anything referencing the day-job stack belongs to the day job>`
- Never invent cross-org links. Treat your orgs as separate; don't tie an item in one to an item in
  another unless the evidence is explicit.

## Meetings to skip in prep

`meeting-prep` should not build a brief for these. Adjust to taste:

- Personal and non-work events — workouts, training, medical appointments, family, travel, meals,
  focus blocks, OOO, reminders, holds with no attendees
- `<any org whose meetings you don't want prepped>`
- Ambiguous work-vs-personal: prepare only if there are external attendees or a clear agenda

## Domain tags

Tags used in daily logs, so `weekly-review` can group the week by domain:

`<#tag>`, `<#tag>`, `<#tag>`, `<#tag>`

## External updates — topic buckets

Topics `morning-briefing` searches for current external news. Give each a scope and a reason it
matters, so the "why this matters to you" tag can be written honestly. Keep to 3–5 buckets; the
whole section is capped at ~6–10 items.

- **`<bucket name>`** — `<what to look for>`. Relevance: `<why you care>`
- **`<bucket name>`** — `<what to look for>`. Relevance: `<why you care>`
- **`<bucket name>`** — `<what to look for>`. Relevance: `<why you care>`

Delete this section to turn the Updates section off entirely.

## Name normalizations

People whose names show up inconsistently across sources. Prevents duplicate CRM profiles and
double-counted touchpoints.

| Seen as | Normalize to |
|---|---|
| `<variant>` | `<canonical>` |

## Transcription corrections

Proper nouns that speech-to-text reliably mangles. Applied to distilled prose in `meeting-ingest`
but **never** inside verbatim quotes.

| Mis-transcribed as | Correct to |
|---|---|
| `<wrong>` | `<right>` |

## Expense forwarding

**Required:**

- **Intake address:** `<where your expense tool receives receipts>`
- **Minimum amount:** `<e.g. $75.00>` — items below this are skipped
- **Then one of the two exclusion strategies below.** Without one of them, receipt forwarding stays
  off, because nothing else can tell a card charge from an invoice your finance team pays.

**Strategy A — exclusion list** (preferred):

- **Accounting / AP addresses:** `<ap@, accounts-payable@, accounting@, billing@, finance@, invoices@, payables@ ...>`
  — invoices addressed here are paid by the finance team, not your card, and must **not** be forwarded

**Strategy B — strict confirmation** (when you don't know your AP addresses):

- **`strict-confirmation`:** `enabled` — forward **only** on positive evidence a card was already
  charged: card last four, a transaction/charge ID, or explicit "payment successful" wording. Anything
  that merely reads like an invoice is skipped. This deliberately under-forwards; you'll miss the odd
  receipt but nothing wrong reaches your expense report.

**Optional refinements** — each is discoverable later from a single mis-forwarded receipt, so don't
hunt for them up front:

- **Group inbox aliases:** `<any shared address whose receipts land in your inbox>`
- **Known exclusions:** `<vendors whose invoices are AP-billed rather than card-charged>` — real
  examples matter here; one named case teaches the pattern better than a rule
- **Registered sender addresses:** `<addresses your expense tool accepts mail from>`

## Meeting ingest

Only needed if you use the `meeting-ingest` skill.

- **Job tag:** `<short slug written into note frontmatter and the state filename, e.g. work>`
- **Upstream ingest skill:** `<name of the skill that owns your note-source workflow, if you have one>`
- **Expected document-source account:** `<account the notes are published under — a mismatch means STOP>`

## Conventions

- **Capitalization:** `<any brand or product name with non-obvious casing>`
- **Memory writes:** auto-memory is user-triggered only by default. Scheduled runs must not write to
  it. Note any sanctioned exception here — `relationship-cms` needs one if you want it mirroring
  people entries.
- **Mail scope:** every mail search must be scoped to the inbox. Enforce at the query level, never
  filter after the fact. Archived mail is considered already actioned and must never surface.
- **No fabrication.** If a source has nothing, say so. Cite sources for external facts. Disclose
  uncertainty rather than guessing.
