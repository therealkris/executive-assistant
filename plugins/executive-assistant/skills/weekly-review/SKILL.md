---
name: weekly-review
description: End-of-week cross-domain review — synthesizes daily logs, email, and calendar into what got done by domain, carryovers, wins, and next week's top priorities. Use when the user asks for a weekly review, EOW summary, "how did the week go", "wrap up the week", "what happened this week", or when the scheduled weekly run fires.
---

# Weekly Review

Act as the user's executive assistant. Deliver their end-of-week review. Direct and concise — no
fluff.

## Capabilities

**Optional (all of them):** `daily-logs`, `mail`, `calendar`, `action-ledger`, `outbound-email`

- **All absent** → nothing to review. Say so and stop.
- `daily-logs` absent → skip section 1. Sections 2–5 still work from email and calendar, and the
  week summary is built from those instead.
- `action-ledger` absent → skip section 4. Carryovers then come only from the daily logs, with no
  way to record completions — say so in one line rather than asking a question nothing can act on.
- End with the one-line "Not configured: …" note from `capabilities.md`.

## Load first

- `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` — **read this first.** Where the config lives, what
  to do if it's missing, and how to degrade when a tool isn't configured. Then read the config.
- `${CLAUDE_PLUGIN_ROOT}/shared/scan-sources.md`
- `${CLAUDE_PLUGIN_ROOT}/shared/action-ledger.md` — needed for section 4

Run in sequence. Format cleanly, lead with the week dates, keep it scannable.

---

## 1. Week in review — from daily logs

Read all daily log files for this week (Mon–Fri) from the daily logs folder in `config.md`.
Per day that has a log, pull accomplishments, tasks captured (matched against the **domain tags**
listed in the config), and any notes or decisions worth surfacing.

Synthesize to week level:

- What actually got done, **grouped by the config's domain tags**
- Tasks captured but not completed (carryovers)
- Decisions or notable context recorded during the week
- Days with no log — flag as "no log captured"

## 2. Email — week in review

Search this week (Mon–Fri), scoped to the inbox. Summarize:

- Key threads that moved — operations, legal, financial, product, and any other areas the config
  marks as high-priority
- Anything unresolved needing attention next week
- Any emails that should have been acted on but weren't

## 3. Calendar — week recap

Pull this week's events. Note:

- Key meetings that happened
- No-shows, cancellations, or rescheduled items worth flagging
- Meetings that produced action items, where visible from context

Apply the calendar attribution rules in `config.md`.

## 4. Open action items — the weekly close-out

The one pass each week where the list gets honest. Per `${CLAUDE_PLUGIN_ROOT}/shared/action-ledger.md`:

1. **Reconcile**, window **the last 21 days**, pulling from meeting notes plus anything in sections
   1–3 the user visibly took on this week.
2. **Report the week's movement first** — items closed this week by status (`done` / `dropped` /
   `delegated`), and items opened this week. Two lines, not a table. Movement is the number that
   tells the user whether the list is working.
3. **Then the open list**, grouped by the config's domain tags, **stale first** with ages.
4. **Walk the stale items individually.** This is the difference between the weekly review and the
   daily wrap: for each item open 21+ days, ask directly whether it is done, dropped, or still real.
   An item the user re-commits to gets a `bumped:` date so the clock restarts and the record shows a
   deliberate choice. Nothing is auto-closed, ever.
5. **Record whatever they say** per the **Close** routine — resolve to exactly one ID, echo before
   writing, write back to the origin meeting note, confirm with counts.

If there are no stale items, say so in one line. It is a good week and worth naming.

## 5. Wins + what's next

- 2–3 things that genuinely moved forward this week — honest, not cheerleading
- Top 3 priorities for next week across all domains, drawn from what is still open in section 4 —
  not invented alongside it

---

## Optional: send by email

This review is delivered in chat by default. If the user asks for it by email, use
`${CLAUDE_PLUGIN_ROOT}/shared/email-delivery.md` with KICKER `WEEKLY REVIEW`, HEADLINE the week
date range, SUBJECT `Weekly Review — <week of date>`, the **Wins + What's Next** block as the lead
callout, action-item IDs printed next to their items so answers can be brought back into a session, empty-section mode `report-nothing`, and footer `— End of review —`.
