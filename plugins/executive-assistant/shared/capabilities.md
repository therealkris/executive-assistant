# Capability Contract

**Read this before any skill in this plugin does work.** It defines which tools a skill needs, how
to tell whether they're available, and what to do when they aren't.

The governing rule: **a capability the user didn't configure is skipped, never guessed at and never
treated as an error.** No skill fabricates data for a source it can't read, and no skill fails
because an optional tool is missing.

---

## Where config lives

The config location depends on the environment, because the two places Claude runs have different
filesystem reach:

- **Claude Code (terminal)** can read and write `~/.claude/`, so `${CLAUDE_PLUGIN_DATA}` works.
- **Cowork (desktop app)** can only reach folders the user has explicitly connected.
  `${CLAUDE_PLUGIN_DATA}` resolves to a path under `~/.claude/` that is **not reachable** there.

So resolve in this order and use the first that exists:

1. `${CLAUDE_PLUGIN_DATA}/config.md` — preferred. Survives plugin updates. Available in Claude Code.
2. `<connected folder>/.executive-assistant/config.md` — the Cowork-friendly location. Check each
   folder the user has connected and use the first match. Also survives plugin updates, and the user
   can see and back it up.
3. `${CLAUDE_PLUGIN_ROOT}/shared/config.md` — legacy / development only. If the config is here and
   neither location above exists, copy it to the best available location above and use the copy.
   Mention the move in one line.
4. **None exist** → the plugin is not set up. Do not attempt the task, do not guess values.
   Say exactly this and stop:

   > This plugin isn't set up yet. Run the `setup` skill and I'll walk you through it — it takes
   > about two minutes and you won't need to edit any files.

If more than one location has a config, use the first in the order above and say which one you used,
so a stale duplicate can't quietly change behavior.

Never write config into `${CLAUDE_PLUGIN_ROOT}`. That directory is replaced on every plugin update,
which would silently discard the user's settings.

## Detecting a capability

**Tool presence is not proof of availability.** Two failure modes make presence-based detection wrong
in both directions:

- A connector can be listed but **unauthorized** — its tools appear, then every call fails with an
  auth error. Authorizing needs an interactive flow the user must do in their Claude settings.
- A connector can be reported as needing authorization and still **work**, because it finished
  connecting after the session started.

So confirm a capability with **one cheap read call**, not by looking at the tool list. Prefer a call
that lists something small: accounts, teams, labels, calendars. If it returns data, mark `enabled`.
If it errors, mark `not configured` and, when the error is clearly about authorization, tell the user
that connector needs authorizing in their Claude settings.

**When several tools can serve one capability** — for example two mail connectors — don't guess. Pick
one, record the choice in the config's *Connector rules*, and note that reading and writing may need
different tools: some connectors can read a thread but cannot create a draft attached to it. The
config, not the skill, is where that choice belongs.

## The capabilities

The config's **Capabilities** table assigns each of these a status. `enabled` means the user
confirmed the tool during setup. Anything else — `not configured`, `unavailable`, a missing row, or a
missing table — means treat it as absent.

| Capability | Powers |
|---|---|
| `mail` | Reading the inbox: triage, briefing email sections, weekly email recap, prep context |
| `mail-draft` | Creating reply drafts. Distinct from `mail` — some setups can read but not draft in-thread |
| `calendar` | Today's and tomorrow's schedule, meeting detection, week recap |
| `chat` | Slack/Teams scans for items needing a reply |
| `issue-tracker` | Issues due today, end-of-day activity |
| `meeting-notes` | Reading the local meeting-notes knowledge base |
| `meeting-ingest-source` | Writing new meeting notes from a document source or Notion |
| `outbound-email` | Sending briefings and prep briefs as formatted email. Satisfied by **any** tool that can send mail — a dedicated automation sender if configured, otherwise the mail connector's own send capability. Only absent when nothing at all can send |
| `web-search` | The external Updates digest |
| `expense-tool` | Receipt forwarding |
| `voice-profile` | The stored writing-voice model used when drafting |
| `people-crm` | Relationship profiles used for tone and attendee context |
| `daily-logs` | The daily log files the weekly review synthesizes |
| `action-ledger` | The durable action-item ledger. Status lives here, not in the meeting notes the index regenerates from |
| `memory-mirror` | Permission to mirror people entries into auto-memory |

## How each skill degrades

Every skill declares **Required** and **Optional** capabilities. The pattern:

- **A required capability is absent** → do not run. State plainly which capability is missing and
  that `setup` can configure it. Do not partially execute.
- **An optional capability is absent** → skip that section entirely. Do not render an empty section,
  do not apologise repeatedly, do not substitute a guess.
- **Report the skips once.** End the output with a single line listing what was skipped, so the user
  can tell the difference between "nothing happened today" and "that source isn't hooked up":

  > Not configured: chat, issue tracker. Run `setup` to add them.

  Omit the line entirely when everything the skill wanted was available.

That last point matters more than it looks. A briefing that silently drops its chat section is
indistinguishable from a briefing where chat was quiet — and the second is information while the
first is a misconfiguration. Always make the difference visible.

### Reference table

| Skill | Required | Optional |
|---|---|---|
| `setup` | *(none — it runs before anything is configured)* | all |
| `inbox-triage` | `mail` | `mail-draft`, `voice-profile`, `people-crm` |
| `morning-briefing` | at least one of the optional set | `mail`, `chat`, `calendar`, `issue-tracker`, `meeting-notes`, `action-ledger`, `web-search`, `outbound-email` |
| `eod-wrap` | at least one of the optional set | `mail`, `chat`, `calendar`, `meeting-notes`, `action-ledger`, `issue-tracker`, `outbound-email` |
| `weekly-review` | at least one of the optional set | `daily-logs`, `mail`, `calendar`, `action-ledger`, `outbound-email` |
| `meeting-prep` | `calendar` | `mail`, `chat`, `meeting-notes`, `issue-tracker`, `people-crm`, `web-search`, `outbound-email` |
| `meeting-ingest` | `meeting-ingest-source` | — |
| `voice-profile` | at least one of `mail`, `chat`, `meeting-notes` | — |
| `relationship-cms` | at least one of `mail`, `chat`, `meeting-notes` | `outbound-email`, `memory-mirror` |
| `action-review` | `action-ledger` | `meeting-notes`, `mail`, `chat`, `issue-tracker` |
| `receipt-forward` | `mail`, `expense-tool` | — |

For the three briefings, "at least one of the optional set" means: if **every** listed source is
absent there is nothing to report, so say so and stop rather than sending an empty briefing.

### Specific degradations worth naming

- **`outbound-email`** → prefer the dedicated automation sender when the config names one; otherwise
  fall back to the mail connector's send tool, sending from the user's own account. Treat the
  capability as absent **only when no tool can send mail at all**. When it is genuinely absent,
  deliver the full output in chat instead — everything still runs, only delivery changes. Note it
  once: "Delivered in chat — no way to send mail is configured."
- **`mail-draft` absent but `mail` present** → triage still classifies and labels. Report the
  classification and note that drafts were not created.
- **`voice-profile` absent** → draft in a neutral-professional tone, and say so in the summary, since
  the drafts will read less like the user than they eventually should.
- **`people-crm` absent** → neutral-professional tone; skip the sender/attendee lookup step.
- **`web-search` absent, or no topic buckets defined** → omit the Updates section, no placeholder.
- **`memory-mirror` absent** → `relationship-cms` writes profile files only and says the mirror was
  skipped. This is the safe default; memory writes need explicit permission.
- **`action-ledger` absent** → the degradation differs by skill, because they don't all have the
  same fallback available:
  - `morning-briefing` and `eod-wrap` list open action items straight from meeting notes — the
    pre-ledger behavior. Nothing remembers a completion, so an item resurfaces every run until its
    note is edited by hand. Say so in one line, and don't ask a close-out question no skill can act
    on.
  - `weekly-review` **skips its action-item section entirely.** `meeting-notes` is not among its
    optional capabilities, so it has no source to fall back to; carryovers come from the daily logs
    alone.
  - `action-review` requires the capability. A list with no state is the problem it exists to solve.

  **A briefing never creates the ledger file** — a scheduled 7am run must not quietly start writing
  state the user never asked for; it reports the gap and falls back. `setup` creates it during
  configuration, and `action-review` may create it when a user invokes it interactively and agrees.
- **A config section is present but empty** (e.g. no chat channels listed) → treat that capability as
  absent, exactly as if the row said `not configured`.

## Optional config sections

Some config sections aren't tools but still gate behavior. If missing or empty, skip the dependent
work silently:

| Section | Gates |
|---|---|
| Calendar attribution | Multi-org meeting attribution. Absent → don't attempt attribution; don't invent org boundaries. |
| Meetings to skip in prep | The prep filter. Absent → prep every work-looking meeting; still skip obvious personal events. |
| Domain tags | Grouping the weekly review by domain. Absent → group by whatever structure the logs actually show. |
| External updates topic buckets | The Updates section. Absent → omit the section. |
| Name normalizations | Merging name variants. Absent → no merging. |
| Transcription corrections | Fixing mangled proper nouns. Absent → leave text as-is. |
| Expense forwarding | Receipt rules. Absent → `receipt-forward` cannot run safely; treat `expense-tool` as absent. |
| Action ledger path | Where action-item state lives. Absent → treat `action-ledger` as absent, whatever the capability row says. |
