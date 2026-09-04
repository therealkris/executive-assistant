---
name: setup
description: Guided first-time setup for the executive-assistant plugin. Detects which tools are connected, asks the user a short series of multiple-choice questions, and writes the config file for them — no file editing required. Use when the user says "set up", "set me up", "configure this plugin", "get started", "onboard me", "finish installing", when they ask why a skill says it isn't configured, or when they want to change or review existing settings.
---

# Setup

Walk the user through configuring this plugin. **They should never have to open or edit a file.**
Assume no technical background: no paths typed by hand, no JSON, no YAML, no terminal.

You ask; you write the config. Keep it to a few minutes.

## Ground rules

- **Use the multiple-choice question tool** for anything that can be a choice. Reserve free text for
  genuinely open answers: their name, role, org names, email addresses.
- **Detect before asking.** If a connector can tell you the answer — their email accounts, their chat
  channels — look it up and ask them to confirm rather than recall.
- **Batch questions.** Ask several related things at once rather than one at a time.
- **Never invent a value to fill a gap.** An unanswered question becomes `not configured`, and the
  dependent skill skips that work. That is a correct, supported outcome — say so, so the user doesn't
  feel they've failed a step.
- **Anything can be skipped.** Every question needs a "Skip this" path. Some people only want inbox
  triage.
- Read `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` first so you know what each capability gates.

---

## Step 1 — Check for existing config

Resolve the config per `capabilities.md`. Then:

- **`${CLAUDE_PLUGIN_DATA}/config.md` exists** → this is a re-run. Summarize the current setup in a
  few lines (which capabilities are enabled, which aren't), then ask whether they want to
  **add a missing tool**, **change something specific**, or **start over**. Don't re-interview from
  scratch by default.
- **Only the legacy copy at `${CLAUDE_PLUGIN_ROOT}/shared/config.md` exists** → migrate it: copy to
  `${CLAUDE_PLUGIN_DATA}/config.md`, tell them in one line that settings now live somewhere that
  survives plugin updates, then offer to review it.
- **Neither exists** → first-time setup. Continue.

Open with one or two sentences: you'll ask a handful of questions and write their settings for them;
they can skip anything; they can re-run `setup` any time to change it.

## Step 2 — Detect what's connected

Work out which capabilities are actually available **before** asking about them.

**Verify with a real call. Do not trust the tool list.** A connector's tools can be listed while every
call fails with an authorization error, and a connector reported as needing authorization can turn out
to work because it finished connecting after the session started. Presence-based detection is wrong in
both directions.

For each capability, make **one cheap read call** and mark `enabled` only if it returns data:

| Capability | Cheap probe |
|---|---|
| `mail` / `mail-draft` | List configured mail accounts, or list labels |
| `calendar` | List calendars |
| `chat` | Search channels for a common term (see Step 8 — enumeration isn't available) |
| `issue-tracker` | List teams or projects |
| `meeting-ingest-source` | List a small number of recent docs, or query the notes database |
| `outbound-email` | Check for **any** send-capable tool: a dedicated automation sender's inboxes, or the mail connector's own send tool. `enabled` if either exists |
| `web-search` | Available if a search tool is present; no probe needed |

If a probe fails with something that reads like an authorization problem, mark the capability
`not configured` **and tell the user that connector needs authorizing in their Claude settings** —
that's actionable, whereas "not available" isn't.

Two things to handle explicitly:

- **`mail` and `mail-draft` are separate.** Reading an inbox does not imply being able to create a
  draft attached to an existing thread. Probe and record them independently.
- **Several tools may serve one capability** — two mail connectors, two chat connectors. Don't guess.
  If reading and drafting are better served by different connectors, record that split in the config's
  *Connector rules* with a one-line reason. This is the single most valuable thing setup can capture,
  because it's the kind of detail a user would otherwise discover only by getting broken output.

Then tell the user what you found, in plain language — no tool names, no `mcp__` identifiers:

> Here's what I can see connected: **email**, **calendar**, and **Slack**. I don't see an issue
> tracker or an expense tool — I'll leave those off, and you can add them later by running `setup`
> again.

If something they expect is missing, explain that connecting tools happens in their Claude settings,
not here, and that a missing tool only means the related sections get skipped — nothing breaks.

**Do not ask about capabilities you couldn't detect.** Asking someone to configure Slack channels
when Slack isn't connected wastes their time and produces settings that don't work.

## Step 3 — Ask what they actually want

**Detection tells you what's possible. It does not tell you what they want.** Never interview someone
about a feature before they've said they want it — most people will use a subset, and every question
about an unwanted feature is wasted effort that makes setup feel long and bureaucratic.

Present the features whose tools you detected as a **multi-select menu**, each with a one-line
description of what it does for them. Something like:

> Which of these would you like? Pick as many as you want — you can add more later.
>
> - **Inbox triage** — sorts new email and drafts replies for you to review
> - **Morning briefing** — a daily email with your schedule, waiting messages, and priorities
> - **End-of-day wrap** — what's unfinished and what tomorrow looks like
> - **Action item tracking** — keeps one list of what you owe people across meetings, email and chat, and remembers what you've told it is finished so it stops coming back
> - **Weekly review** — a Friday summary of the week
> - **Meeting prep** — a brief before each meeting, with background on who you're meeting
> - **Meeting notes** — files your meeting notes automatically
> - **Writing voice** — learns how you write so drafts sound like you
> - **Contacts** — keeps notes on people you work with regularly
> - **Receipt forwarding** — sends receipts to your expense tool

Omit any line whose tools you didn't detect — **except the file-backed features**, which need no
connector at all. Action item tracking and daily logs are a folder and a file; there is nothing to
probe for in Step 2, so never omit them on detection grounds. Offering them is the only way they
ever get created.

Then:

- **Only interview for what they picked.** Everything unpicked is written as `not configured` and
  never mentioned again during setup.
- **Ask before the details, per feature.** When you reach a feature's detail questions, if it needs
  more than one piece of information, say so up front — "this needs three things" — so they can decide
  whether it's worth it before answering the first question. A feature that collects one answer and
  then refuses to turn on because two more were missing is the worst possible outcome; it wastes their
  time and reads as a bug.
- If a feature turns out to need something they can't supply, say so immediately, offer the safe
  fallback if one exists, and move on. Don't leave it half-configured.

Tell them plainly that picking fewer things is normal and nothing is degraded by leaving features off.

## Step 4 — Identity

Free text, asked together in one message:

- Their full name, and what they'd like to be called
- Their role and organization — a sentence is fine
- Any other org they work with (a second job, a company they own, a board seat). This is what lets
  the briefings attribute meetings to the right place.
- Anyone whose name should be recognized — a co-founder, a boss, a key colleague

Then offer tone as a choice: **direct and concise** / **warm and conversational** /
**formal and detailed** / **match how I write** (which leans on the voice profile once it exists).

## Step 5 — Organizations and email domains

For each org from Step 3, get the email domain. Explain *why* in one line: it's how the assistant
tells colleagues from outsiders, so it knows to research an external attendee before a meeting and
not to bother for internal ones.

If they only have one org and one domain, confirm and move on.

## Step 6 — Accounts

**Detect first.** If the mail connector can list accounts, list them and ask which to use for:

- **Work email** — the account to triage. Default to their primary if there's only one.
- **Other accounts to include in briefings** — multi-select, optional.
- **Where briefings should be delivered** — default to their work email.

Only ask them to type an address if detection found nothing.

**How briefings get delivered.** If mail is connected, email delivery works — don't ask a question that
implies otherwise.

- If a **dedicated automation sender** exists (a service like AgentMail), offer it: briefings arrive
  from a separate address, so they're easy to filter and don't clutter their Sent folder. Record it.
- If not, **default to sending from their own work account** and just tell them: "Briefings will be
  emailed to you from your own account — they'll show up in your Sent folder." No question needed;
  this is the normal case.
- Only if **nothing can send mail** do you mark `outbound-email` as `not configured` and explain that
  briefings will appear in chat instead.

Never disable email delivery just because there's no dedicated sender. A mail connector that can read
can almost always send, and quietly falling back to chat-only is worse than a Sent-folder entry.

## Step 7 — Where files go

**Do not ask for a path.** Offer choices, and create the folders yourself:

- **Inside my notes/workspace folder** (recommended if they have one connected) — offer a sensible
  subfolder and create it
- **In a new folder I'll make for you** — pick a sensible default location and say where it is
- **Skip file features** — mark `daily-logs`, `meeting-notes`, `people-crm`, `action-ledger`, and
  `voice-profile` as `not configured`. The briefings still work off email, calendar, and chat.

Create every folder you record a path for. A path in the config that doesn't exist on disk produces
a confusing failure later.

### Action item tracking needs one file

Only if they chose action item tracking. **One question, then you create the file.**

The ledger is a single markdown file — offer a name (`Action Items.md`) inside their notes location
and create it with the `## Open` and `## Closed` headings, per
`${CLAUDE_PLUGIN_ROOT}/shared/action-ledger.md`. Record the path as **Action ledger** and set
`action-ledger: enabled`.

Two things to tell them, in one line each, because they are the reasons this exists:

- **Nothing is ever auto-closed.** Items leave the list because they said so, not because they got old.
- **This file is durable.** The meeting search index is regenerated from the notes and is safe to
  delete; this one is not, and is the only place a completion is recorded.

If they already have a hand-maintained list of open items, offer to seed the ledger from it rather
than starting empty — then tell them the old file is superseded, and let *them* decide whether to
delete it. Do not delete or move a file the user wrote.

### Meeting notes need a little more than a folder

Only if they chose meeting notes or meeting prep. The meeting skills read a **generated search index**
over the notes, and it needs scaffolding:

1. **Create the structure** under their notes location:
   `meetings/`, `meetings/transcripts/`, `meetings/.state/`, `meetings/.index/`
2. **Check `python3` is available.** Run `python3 --version`. If it's missing, say plainly that the
   meeting index needs Python and the skills will fall back to reading notes directly — slower, and no
   full-text search across transcripts, but fully functional. Don't treat it as fatal.
3. **Build the index once** by running the bundled script:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_index.py" <meetings dir>`
   On an empty folder this produces an empty `INDEX.md` and `meetings.db`. Do it anyway — it proves the
   whole path works now rather than failing on the first real ingest at 6am.
4. **Record the paths in the config**, with the script path left as
   `${CLAUDE_PLUGIN_ROOT}/scripts/build_index.py`. The script ships with the plugin; the user never
   supplies it and should never be asked for it.

The index is a **disposable derivative** — markdown notes are the source of truth, and the index can be
deleted and rebuilt at any time. Say that, because it's the reassurance that makes the whole thing
low-stakes.

## Step 8 — Chat channels (only if they chose a feature that uses chat)

**You probably cannot enumerate their channels.** Chat connectors typically expose *search*, not
list-all: searching requires a query term, and a multi-word query matches nothing. So the
"show a list, let them pick" approach doesn't work here.

Do this instead:

1. Ask them to name the channels they'd want watched — free text, a few names. Tell them they can add
   more later, and that direct messages are always included.
2. **Verify each name by searching for it individually**, one term per search. Confirm the ones you
   find and report the ones you don't, so a typo doesn't silently produce a channel that never
   matches anything.
3. **Include private channels in the search.** Most connectors default to public channels only, so a
   private-channel search parameter must be set explicitly. The channels that matter most to an
   executive are often the private ones — a default-only search will miss them and look like the
   channel doesn't exist.

Offer "just direct messages" and "skip chat" as options throughout.

## Step 9 — Optional refinements

Introduce these as optional and let them skip the lot in one go. Ask only about capabilities that are
enabled.

- **Recurring meetings that belong to a different org** — only if they named more than one org in
  Step 4. This is what stops a day-job meeting appearing in the wrong briefing.
- **Meetings never to prep** — offer sensible defaults as a multi-select (personal appointments,
  workouts, focus blocks, holds with no attendees) plus anything they add.
- **News topics for the daily Updates digest** — only if `web-search` is enabled. Get 3–5 topics and,
  for each, one line on why it matters to them, so the digest can say why an item is relevant. If
  they skip, the Updates section is omitted.
- **Tags used in daily logs** — only if `daily-logs` is enabled.
- **Name spellings to normalize** — e.g. someone who appears as both "Sean" and "Shaun". Prevents
  duplicate profiles.
- **Words transcripts get wrong** — company or product names speech-to-text mangles.
- **Memory mirroring** — ask explicitly whether the relationship CRM may also write contact summaries
  into Claude's memory. **Default to no.** Only set `memory-mirror: enabled` on a clear yes.

### Receipt forwarding — ask for everything at once

Only if they chose receipt forwarding in Step 3. **This needs three things, and you must ask for all
three in one pass.** Collecting the intake address, then refusing to enable the feature because two
other answers are missing, is the failure mode to avoid — it wastes the user's time and reads as a bug.

Open by naming the cost up front:

> Receipt forwarding needs three things from you. Takes about a minute.

**1. Where receipts go** — the intake address for their expense tool (e.g. an Expensify receipts
address). Free text.

**2. Minimum amount** — a multiple choice: **$25** / **$50** / **$75** / **no minimum**. Anything below
is skipped, which keeps small recurring charges off the report.

**3. Which invoices to exclude.** This is the one that gets skipped, so explain the stakes in one
line: *some invoices are paid by the finance team, not your card, and those must not land on your
expense report.* Then — critically — **offer a default list rather than asking them to invent one:**

> Most companies route these to shared addresses. I'll exclude anything addressed to:
> `ap@`, `accounts-payable@`, `accounting@`, `billing@`, `finance@`, `invoices@`, `payables@`
> — at any domain. Does that cover it, or do you use something different?

Offer: **use these defaults** / **add to the list** / **I don't know**.

**If they don't know**, do not refuse and do not turn the feature off. Offer strict mode:

> I'll only forward emails that explicitly confirm a card was charged — a card's last four digits, a
> transaction ID, "payment successful". Anything that merely looks like an invoice gets skipped. You'll
> miss the occasional receipt, but nothing wrong will reach your expense report.

Record that choice in the config as a strict-confirmation flag so `receipt-forward` knows to require
positive evidence of a card charge rather than relying on an exclusion list. **Strict mode is a valid
enabled state** — say so, so they don't think they failed the step.

Optionally, if they volunteer them: group inbox aliases whose receipts land in their inbox, other
sender addresses registered with their expense tool, and any vendor known to be AP-billed. Don't
chase these — they're refinements, and each is discoverable later from a mis-forwarded receipt.

Only mark `expense-tool` as `not configured` if they decline to give an intake address, or explicitly
ask to leave the feature off. Missing refinements are never a reason to disable it.

## Step 10 — Write the config

Write it where this environment can actually reach, following the structure of
`${CLAUDE_PLUGIN_ROOT}/shared/config.example.md`.

**Pick the location by trying, not by assuming** — see *Where config lives* in `capabilities.md`:

1. Try `${CLAUDE_PLUGIN_DATA}/config.md`. This works in Claude Code (terminal).
2. If that path isn't reachable — which is the normal case in the Cowork desktop app, where only
   folders the user has connected are accessible — write to
   `<connected folder>/.executive-assistant/config.md` instead, using the folder that holds their
   notes or work files. Create the directory. Tell them the path in plain language and that it's
   theirs to keep and back up.
3. If no location is writable, don't fake success. Say you couldn't save settings, name what you'd
   need (a connected folder), and stop.

Whichever you use, state which one, once. A user who later can't find their settings needs to know
where they went.

Requirements:

- Include a **Capabilities** table with an explicit row for **every** capability in
  `capabilities.md` — `enabled` or `not configured`. A missing row and a `not configured` row behave
  the same, but writing them all out makes the file self-documenting and makes the next `setup` run
  easy.
- **Omit sections they skipped** rather than leaving placeholder text. A section containing
  `<placeholder>` is worse than no section: skills may read the placeholder as a real value.
- Fill in real values only. Never carry an example value over from the template.
- Add a comment line at the top noting the file was generated by `setup` and can be changed by
  re-running it.

## Step 11 — Confirm and offer next steps

Show a short plain-language summary:

> **You're set up.** Working: inbox triage, morning briefing, end-of-day wrap, meeting prep.
> Not configured: issue tracker, expense forwarding, meeting notes — briefings will just skip those
> sections. Run `setup` again any time to add them.

Then mention that these can run on a schedule — a briefing waiting at 7am rather than something they
have to remember to ask for — and offer, as choices:

1. **Try one now** — suggest the most useful skill given what's enabled, and run it. This is the best
   confidence-builder; prefer it.
2. **Set the schedules up for me** — create them now. See *Scheduling* below.
3. **Just show me how, I'll do it later** — print the instructions. See *Scheduling* below.
4. **Nothing for now** — and say in one line that they can ask about schedules any time.

Make option 3 a real option, not a consolation prize. Plenty of people want to see what they're
agreeing to before anything is created on a timer, and someone who's just answered a dozen questions
may simply be done for now.

### Scheduling

**Which document to use depends on the environment:**

- **Cowork desktop app** → `${CLAUDE_PLUGIN_ROOT}/scheduled-tasks/COWORK.md`. Written for
  non-technical users: plain-language phrases they can say, no cron. If they chose option 3, show them
  the relevant lines from it — only for features they configured — rather than dumping the whole file.
- **Claude Code (terminal)** → `${CLAUDE_PLUGIN_ROOT}/scheduled-tasks/REGISTER.md`, which has the cron
  expressions and thin task prompts.

Whichever path:

- **Only schedule tasks whose required capabilities are enabled.** Never schedule `receipt-forward`
  with no expense tool, or `meeting-prep` with no calendar. A task that runs on a timer and reports it
  can't do anything is noise, and it erodes trust in everything else.
- **Describe schedules in plain terms** — "weekday mornings at 7" — never a cron expression.
- **Tell them the app-open caveat, once.** In Cowork, scheduled tasks only run while the app is open;
  if it's closed when one is due, it runs on next launch. Someone expecting a 7am email on a closed
  laptop will otherwise think it's broken. Say it plainly and move on — it's usually fine, since they
  get the briefing when they sit down.
- **Suggest a starting set rather than all of them.** Morning briefing, end-of-day wrap, and inbox
  triage are enough to be useful without being noisy. Meeting prep once they trust the briefings. The
  rest when they miss them. Ten scheduled tasks on day one is how people end up turning everything
  off.
- If they'd rather not decide, offer the default set from `COWORK.md` as a single choice.

## If setup can't complete

If no capabilities at all are detected, don't write a config full of `not configured` rows. Explain
that no tools appear connected, that tools are connected in their Claude settings, and that they
should run `setup` again afterward. Offer to explain what each tool would enable.
