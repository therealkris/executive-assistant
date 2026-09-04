---
name: eod-wrap
description: Weekday end-of-day wrap — unactioned email, chat needing reply, tomorrow's calendar setup, today's meeting key points and action items, and issue-tracker activity. Emails a formatted HTML version. Use when the user asks for an EOD summary, end-of-day wrap, "how did today go", or when the scheduled EOD run fires.
---

# EOD Wrap

Act as the user's executive assistant. Deliver their end-of-day wrap. Direct and concise. No padding.

## Capabilities

**Optional (all of them):** `mail`, `chat`, `calendar`, `meeting-notes`, `action-ledger`,
`issue-tracker`, `outbound-email`

Skip the section for any absent capability — sections 1–6 below map one-to-one onto these.

- **All of them absent** → nothing to wrap. Say so and stop.
- `outbound-email` absent → **only** when no tool can send mail at all. Prefer a dedicated
  automation sender; otherwise send with the mail connector from the user's own account. See
  `email-delivery.md` for the ordering. Genuinely absent → deliver in chat and skip section 7.
- `meeting-notes` absent → skip section 4. Section 5 still runs from the ledger.
- `action-ledger` absent → section 5 degrades to a read-only list of today's items; see that section.
- End with the one-line "Not configured: …" note from `capabilities.md`.

## Load first

- `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` — **read this first.** Where the config lives, what
  to do if it's missing, and how to degrade when a tool isn't configured. Then read the config.
- `${CLAUDE_PLUGIN_ROOT}/shared/scan-sources.md`
- `${CLAUDE_PLUGIN_ROOT}/shared/action-ledger.md` — needed for section 5
- `${CLAUDE_PLUGIN_ROOT}/shared/email-delivery.md` — needed for section 7

Keep the full report under a minute to read.

---

## 1. Email — EOD scan

Emails received today that haven't been acted on. Scope every search to the inbox and add
`-in:sent -category:promotions -category:social` to cut noise. Archived messages are considered
already actioned and must not surface.

Check every account listed for briefing scope in `config.md`.

Surface:

- Anything that still needs a reply
- Anything with deadlines or time-sensitive flags
- Flag anything touching the orgs, vendors, or subject areas the config marks as high-priority —
  typically legal, financial, incidents, and key partners

## 2. Chat — EOD scan

Per `scan-sources.md`. Only items needing a reply or action from the user.

## 3. Tomorrow's setup

Pull tomorrow's calendar:

- Events in time order
- Flag any needing prep tonight
- Note the **first hard commitment** so the user knows when their morning is locked
- Apply the calendar attribution rules in `config.md`. Do not invent cross-org links — treat the
  user's orgs as separate.

## 4. Today's meetings — key points & action items

Review meeting notes dated today — match today's date against the filename and/or the `date:`
frontmatter. **Do not fabricate:** if a meeting happened today but no note exists yet, say so and
invent nothing. (If `meeting-ingest` runs on a frequent cadence, today's notes are usually already
present.)

Per meeting dated today:

- Title and a 1–2 line summary of key points / decisions
- Open action items (`- [ ]`) where the user is owner, or the owner is unspecified or shared

If no notes are dated today, say so in one line and skip to section 5.

## 5. Open action items — overview and close-out

This is the section that makes the wrap worth answering. It runs whether or not there were meetings
today.

**With `action-ledger` enabled:**

1. **Reconcile** per `${CLAUDE_PLUGIN_ROOT}/shared/action-ledger.md` — pull in today's meeting
   action items from section 4, plus anything from sections 1–3 the user has visibly taken on. New
   items get IDs; anything already tracked, open or closed, is skipped.
2. **Show what is still open**, grouped by org, **stale items first** under their own sub-heading
   with their age. Cap the routine list at the ~12 most pressing and say how many were not shown —
   never silently truncate. Stale items are never cut.
3. Close with counts: `21 open · 4 stale · 2 due this week`.
4. Then ask, once:

   > **Close-out:** anything here done, dropped, or handed off? Give me the IDs or describe them and
   > I'll record it — closed items don't come back.

**When the user answers in a session**, follow the **Close** routine in `action-ledger.md`: resolve
each reference to exactly one ID, echo before writing, move the line to Closed, flip the matching
`- [ ]` in the origin meeting note, and confirm with counts. An ambiguous reference is a question,
not a guess.

**Without `action-ledger`**, fall back to listing today's open action items from section 4 only, and
say in one line that completions cannot be recorded until the ledger is set up. Do not ask a
close-out question the plugin cannot act on.

## 6. Issue tracker — today's activity

Per the **activity view** in `scan-sources.md` — Completed today / Moved / Updated, with the
verification caveat.

## 7. Send by email

Per `${CLAUDE_PLUGIN_ROOT}/shared/email-delivery.md`, with:

| Variable | Value |
|---|---|
| KICKER | `EOD WRAP` |
| HEADLINE | today's full date — e.g. "Monday, June 22, 2026" |
| SUBJECT | `EOD Wrap — <short date, e.g. Mon Jun 22, 2026>` |
| Sections | 1 Email — EOD Scan, 2 Chat — EOD Scan, 3 Tomorrow's Setup, 4 Today's Meetings, 5 Open Action Items, 6 Issue Tracker — Today's Activity |
| Empty-section mode | **`report-nothing`** — render every section and state its "nothing" status in normal text |
| Plain text | sections 1–6 **and** the close-out prompt |
| Footer | `— End of wrap —` |

This wrap has **no lead callout box.** Three section-specific rules instead:

- The **"Close-out"** prompt at the end of section 5 renders in the amber callout style from `email-delivery.md`, label bold. Always print the IDs next to the items in the email — the user cannot reply to the email and have it recorded, so the IDs are how they bring answers back into a session.
- In section 5, render the **stale** block first, with its own bold sub-label and each item's age.
- In section 3, **bold the first hard commitment** and state its time clearly.

Send even on quiet days.
