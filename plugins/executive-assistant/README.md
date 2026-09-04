# executive-assistant

A Claude Code plugin that turns recurring executive-assistant work into skills: inbox triage,
morning and end-of-day briefings, a weekly review, action-item tracking, meeting prep, meeting-note
ingest, a voice profile builder, a relationship CRM, and receipt forwarding.

Every personal value — accounts, file paths, chat channels, org names — lives in **one config file**,
written for you by a guided setup skill. The skills themselves contain no names, addresses, or company
details, so the plugin travels between machines and between people.

You don't need every tool it can use. Whatever you haven't connected is skipped, not failed.

## Skills

| Skill | What it does | Typical cadence |
|---|---|---|
| `setup` | Guided configuration — detects your connected tools, asks a few multiple-choice questions, writes your settings. **Start here.** | Once, then as needed |
| `inbox-triage` | Classifies new mail as Archive/Delete/Reply, labels it, drafts in-thread replies in your voice. Never sends. | Every 30 min; every 4 h off-hours |
| `morning-briefing` | Email, chat, calendar, issues due today, open action items, external news, suggestions, priority snapshot. Emails an HTML brief. | Weekday mornings |
| `eod-wrap` | Unactioned mail, chat needing reply, tomorrow's setup, today's meetings, an open-action-item close-out, tracker activity. | Weekday evenings |
| `weekly-review` | Synthesizes daily logs, mail, and calendar into the week by domain, carryovers, wins, next week's priorities. Walks stale action items individually. | Weekly |
| `action-review` | Shows what's still open across meetings, mail, chat and conversation, and records what you say is finished so it stops resurfacing. | On demand |
| `meeting-prep` | Detects an imminent meeting and emails a brief: verbatim agenda, join details, researched attendees, prior context, talking points. Deduped. | Every 30 min during work hours |
| `meeting-ingest` | Pulls completed meeting notes from a document source and Notion into a local knowledge base, gated so in-progress meetings are never captured. | Every 30 min |
| `voice-profile` | Analyzes your sent mail, chat, and call transcripts to incrementally refine a voice profile the other skills draft from. | Nightly |
| `relationship-cms` | Counts touchpoints across mail, chat, and meetings; writes and refreshes people profiles. | Weekly |
| `receipt-forward` | Forwards card-charge receipts above a threshold to your expense tool; excludes AP-billed invoices; labels originals. | Daily |

All eleven are invocable on demand in a session, not just on a schedule.

## Setup

**Install the plugin, then say "set up" in a Claude session.** That's it.

The `setup` skill detects which tools you have connected, asks a short series of multiple-choice
questions, and writes your settings for you. **You never edit a file, type a path, or touch JSON.**
It takes a couple of minutes, and you can re-run it any time to add a tool or change an answer.

To install:

- *From a marketplace*: `/plugin marketplace add <owner>/<repo>` then
  `/plugin install executive-assistant@<marketplace>`.
- *Skills-directory plugin* (no marketplace): copy or symlink this directory into your Claude skills
  directory. Any folder there containing `.claude-plugin/plugin.json` loads on the next session with
  no install step.

Then: `set up`.

### You don't need every tool

Nothing here assumes you have the same tools as anyone else. Each skill declares which capabilities
it **requires** and which are **optional**, and a capability you haven't configured is *skipped, not
failed*. Connect only email and you get working inbox triage plus a briefing built from email alone.
Add a calendar later and meeting prep starts working. Nothing breaks in the meantime.

Skills report what they skipped in a single closing line:

> Not configured: chat, issue tracker. Run `setup` to add them.

That line exists on purpose. A briefing that silently drops its chat section looks identical to a
briefing where chat was quiet — one is information, the other is a misconfiguration, and you should
be able to tell which you're looking at.

See [`shared/capabilities.md`](shared/capabilities.md) for the full contract: the capability list, the
required/optional matrix per skill, and exactly how each one degrades.

### Scheduling

These skills are most useful on a schedule — a briefing waiting at 7am rather than something you have
to remember to ask for. At the end of setup you're offered three paths: have the schedules created for
you, just see the instructions and do it later, or skip it.

- **Cowork desktop app** → [`scheduled-tasks/COWORK.md`](scheduled-tasks/COWORK.md). Plain-language
  phrases you can say, no cron. Note the one real caveat: **scheduled tasks only run while the app is
  open** — if it's closed when a task is due, it runs on next launch.
- **Claude Code (terminal)** → [`scheduled-tasks/REGISTER.md`](scheduled-tasks/REGISTER.md). Cron
  expressions and thin task prompts.

Either way, only tasks whose required capabilities are configured get registered — nothing runs on a
timer just to report it can't do anything.

Validate the plugin before relying on it: `claude plugin validate .`

## How it's organized

```
skills/setup/SKILL.md       the guided interview — start here
skills/<name>/SKILL.md      one skill each, no personal values
shared/capabilities.md      capability contract + degradation rules
shared/action-ledger.md     action-item state: format, IDs, reconcile/close/capture
shared/config.example.md    reference for what setup writes
shared/email-delivery.md    send mechanics + HTML email spec
shared/scan-sources.md      how to read mail, chat, tracker, notes, web
scripts/build_index.py      builds the meeting search index (stdlib only)
scripts/receipt_to_pdf.py   renders body-only receipts to PDF for expense intake (stdlib only)
scheduled-tasks/REGISTER.md cron expressions + thin task prompts
```

`scripts/` holds the two executable files in the plugin, both standard-library-only.

`scripts/receipt_to_pdf.py` turns a body-only vendor receipt into a one-page PDF so
`receipt-forward` always has an attachment to send — expense tools parse attachments, not forwarded
email text. Reads the receipt fields on stdin, writes the PDF to `--out`, no network access.

`scripts/build_index.py` reads the markdown meeting notes and
writes `INDEX.md` plus a SQLite + FTS5 database so meeting lookups don't have to scan every file.
Python standard library only, no network access, no writes outside the meetings directory. Setup runs
it once during configuration to prove the path works.

The index is a **disposable derivative** — notes are the source of truth, and deleting the index is
always safe. If Python isn't available the meeting skills read notes directly: slower, no full-text
transcript search, otherwise identical.

Your filled-in config is **not** in this directory. The plugin's own directory is replaced on every
update, so a config stored here would be silently discarded. `setup` writes it to whichever location
your environment can actually reach:

| Environment | Config location |
|---|---|
| Claude Code (terminal) | `~/.claude/plugins/data/<plugin-id>/config.md` |
| Cowork (desktop app) | `<your connected folder>/.executive-assistant/config.md` |

The split exists because Cowork can only reach folders you've explicitly connected, and `~/.claude/`
isn't one of them. `setup` tells you which path it used. If you have an older install with a config in
`shared/config.md`, it migrates that for you.

Either way the config outlives plugin updates, and in Cowork it's somewhere you can see and back up.

The four non-config shared files exist because the HTML email spec, the inbox-scoping rule, the chat
channel list, and the tracker query logic were each restated in three or four places. They're now
single-sourced: four skills call `email-delivery.md`, five call `scan-sources.md`, four call
`action-ledger.md`, all eleven call `capabilities.md`.

## Why schedules aren't in the plugin

Plugins can't ship scheduled tasks — there's no cron component in the plugin
[component set](https://docs.claude.com/en/docs/claude-code/plugins-reference). Registration is
per-instance and one-time. Each task prompt is a single line that invokes a skill, so all logic
stays in the plugin.

## Maintenance rule

**Logic changes go in the skill. Personal values go in your config file. Nothing goes in a task
prompt.** If you're editing a scheduled task prompt beyond its one invocation line, the change
belongs in one of the other two places.

## Design notes

A few decisions worth knowing before you modify anything:

- **Empty sections are handled per skill, not globally.** Briefings use `report-nothing` — they render
  every section and state its nothing-status, because a missing section is indistinguishable from a
  failed scan. `meeting-prep` uses `omit-empty`. Collapsing these into one default silently changes
  briefing behavior.
- **`inbox-triage` claims precedence over other triage skills.** Several published skills advertise
  near-identical trigger phrases with different account scope and label taxonomy. The constraint is
  deliberate.
- **Triage labels rather than acts.** Nothing is archived, deleted, or sent — only labeled and
  drafted. Review stays with you.
- **Idempotency comes from labels, not tight time windows.** Overlapping run windows are safe by
  design, which is why the lookback is deliberately wider than the cadence.
- **Action-item status lives outside the meeting notes.** The meeting index is a disposable
  derivative, fully regenerated from the notes on every ingest — so a completion recorded in the
  index is erased on the next rebuild, and one recorded only in a note is lost if the note is
  re-ingested. `shared/action-ledger.md` defines a separate append-only ledger with derived,
  stable IDs; closing an item there also flips the checkbox in the origin note as a courtesy, but
  the ledger is what's authoritative. Closed IDs are remembered permanently, which is the specific
  mechanism that stops finished work from resurfacing.
- **Nothing auto-closes an action item.** Items age into "stale" at 21 days and get sorted to the
  top and asked about, but only the user closes one. Auto-archiving keeps the list short by letting
  real work fall off it silently.
- **`meeting-ingest` gates on a 30-minute quiet period.** Streaming transcripts keep a page's
  last-edited timestamp fresh while a meeting is still recording; the quiet period is what
  distinguishes "finished" from "in progress."

## License

MIT — see [LICENSE](LICENSE).
