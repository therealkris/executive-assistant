---
name: morning-briefing
description: Weekday morning briefing — email, chat, calendar, issues due today, open action items, topical external updates, suggestions, and a priority snapshot. Emails a formatted HTML version. Use when the user asks for a morning update, daily briefing, "what's on my plate today", "catch me up", "how does my day look", or when the scheduled morning run fires.
---

# Morning Briefing

Act as the user's executive assistant. Be direct and concise — no fluff, no filler. Match the
communication style declared in the config.

## Capabilities

**Optional (all of them):** `mail`, `chat`, `calendar`, `issue-tracker`, `meeting-notes`,
`action-ledger`, `web-search`, `outbound-email`

Skip the section for any absent capability — sections 1–8 below map one-to-one onto these. Do not
render an empty section and do not guess at its contents.

- **All of them absent** → there is nothing to brief. Say so and stop; don't send an empty briefing.
- `outbound-email` absent → **only** when no tool can send mail at all. Prefer a dedicated
  automation sender; otherwise send with the mail connector from the user's own account. See
  `email-delivery.md` for the ordering. Genuinely absent → deliver in chat and skip section 9.
- `action-ledger` absent → section 5 falls back to scanning meeting notes directly, which is the
  pre-ledger behavior: completions are not remembered, so items resurface until the note is edited.
  Note it in one line.
- `web-search` absent, or no topic buckets in the config → omit section 6 (Updates) entirely.
- End with the one-line "Not configured: …" note from `capabilities.md` so a skipped section is
  distinguishable from a quiet one.

## Load first

- `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` — **read this first.** Where the config lives, what
  to do if it's missing, and how to degrade when a tool isn't configured. Then read the config it
  points to for identity, accounts, paths, chat scope, calendar attribution, and topic buckets.
- `${CLAUDE_PLUGIN_ROOT}/shared/scan-sources.md` — how to read each source
- `${CLAUDE_PLUGIN_ROOT}/shared/action-ledger.md` — needed for section 5
- `${CLAUDE_PLUGIN_ROOT}/shared/email-delivery.md` — needed for section 9

Run sections 1–8 in sequence, then send.

---

## 1. Email triage — last 18 hours

Query each account listed for briefing scope in `config.md`, scoped to the inbox, `newer_than:1d`.

Per message: sender, subject, timestamp, one-line summary, and a recommended action —
**Reply / Archive / Task / Flag**. If Reply, note what to address. If an account has no inbox mail,
say so explicitly.

## 2. Chat — overnight scan

Per `scan-sources.md`. Surface only what needs a reply or action from the user.

## 3. Calendar — today

List today's events in time order: time, title, attendees, location or link.

- Flag conflicts and back-to-back meetings with no buffer
- Note any prep needed today
- Apply the calendar attribution rules from `config.md` — if the user holds multiple roles,
  attribute each meeting to the right org

## 4. Issues due today

Per the **due-today view** in `scan-sources.md`. Flag overdue separately.

## 5. Open action items

**With `action-ledger` enabled** — read the ledger, per
`${CLAUDE_PLUGIN_ROOT}/shared/action-ledger.md`. Reconcile first (it is cheap and idempotent) so
anything captured since yesterday appears.

Show only what is genuinely live this morning: **stale items**, anything **due today or overdue**,
and otherwise the **top few by age**. Cap at ~8 and state how many more are open — the full list
belongs in the EOD wrap and the weekly review, not here. Per item: ID, text, and the due date or age
where it matters.

The morning briefing is **read-only** on the ledger. Do not ask a close-out question here — the
user is starting their day, not auditing a list. Closing happens in `eod-wrap`, `weekly-review`, or
`action-review` on demand.

**Without `action-ledger`** — scan meeting notes from the last 21 days per `scan-sources.md`. Per
item: meeting (date + title), the action item text, owner if noted.

If nothing is open either way, say "no open action items." Carry the most pressing into the priority
snapshot.

## 6. Updates — current and topical

A short digest of *current* external developments, using the **topic buckets defined in
`config.md`**. Follow the web search rules in `scan-sources.md`: real dated sources only, roughly the
**last 7 days**, cite source name and link, skip undated items.

Per item: one tight sentence on what happened, then a brief "why it matters" tag tying it to the
relevance note the config gives for that bucket. **Cap the whole section at ~6–10 items** across all
buckets — signal over volume.

Skip any bucket that yields nothing, silently. If nothing relevant surfaced anywhere, say "no
notable updates today." If the config defines no topic buckets, skip this section entirely.

## 7. Suggestions

Based on everything above. Two groups:

**Tasks I can help with today** — 3–5 specific items drawn from the day's actual context (draft a
reply to a waiting sender, prep a one-pager for a meeting on today's calendar, review a shared doc
before a budget meeting). Per item: a short action title and one line of why. Phrase so the user can
act by replying — e.g. "Reply 'draft the exec update' and I'll build it." Only suggest tasks grounded
in something concrete from the briefing. No generic filler.

**Routines I could automate** — 1–3 recurring patterns worth turning into a scheduled task — e.g.
auto-track new-hire onboarding steps, a daily digest of infrastructure or SaaS alerts, auto-summarize
a stalled vendor thread against its deadline. Per item: a short title and one line on what it would
do. Only suggest routines backed by an **observed repeating pattern** in the day's data — not
speculation.

If a group has nothing well-grounded, say so plainly rather than padding.

## 8. Priority snapshot

The 1–3 things that actually matter today, drawn from sections 1–5. A stale or overdue action item belongs here. No padding. Updates and
Suggestions inform but do not displace the core priorities.

Format the chat output cleanly. Lead with the date. Keep it scannable.

## 9. Send by email

Per `${CLAUDE_PLUGIN_ROOT}/shared/email-delivery.md`, with:

| Variable | Value |
|---|---|
| KICKER | `MORNING BRIEFING` |
| HEADLINE | today's full date — e.g. "Monday, June 22, 2026" |
| SUBJECT | `Morning Briefing — <short date, e.g. Mon Jun 22, 2026>` |
| Lead callout | **PRIORITY SNAPSHOT** (section 8) as a numbered `<ol>` |
| Sections | 1 Email Triage, 2 Chat, 3 Calendar, 4 Issues Due Today, 5 Open Action Items, 6 Updates, 7 Suggestions |
| Empty-section mode | **`report-nothing`** — render every section and state its "nothing" status in normal text. The one exception is the Updates topic buckets, which are omitted individually when empty. |
| Plain text | a clean plain-text version of the full briefing, **sections 1–8** |
| Footer | `— End of briefing —` |

Section-specific rendering:

- **Updates** — group items under the bucket sub-labels that have content; each item bolds its lead phrase and ends with the italic muted "why it matters" tag. Omit empty buckets.
- **Suggestions** — two bold sub-labels, "Tasks I can help with today" and "Routines I could automate," each followed by a list. Bold each action title; keep the reply-to-act phrasing in normal text.

Send even on quiet days.
