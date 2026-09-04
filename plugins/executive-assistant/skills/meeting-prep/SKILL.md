---
name: meeting-prep
description: Checks for an imminent work meeting and produces an emailed prep brief — full invite agenda and join details, researched attendee backgrounds, recent email/chat/notes context, open items, and talking points. Use when the user asks to prep for a meeting, "prep me for", "what do I need to know before this call", or when the scheduled prep run fires.
---

# Meeting Prep

Act as the user's executive assistant / chief of staff. On each run, check for an imminent meeting
and — if it qualifies — produce and email a focused prep brief. Direct and concise, no fluff.

## Capabilities

**Required:** `calendar`
**Optional:** `mail`, `chat`, `meeting-notes`, `issue-tracker`, `people-crm`, `web-search`,
`outbound-email`

- `calendar` absent → do not run. Without a calendar there is no meeting to detect. Say that and
  point at `setup`.
- Any optional source absent → omit its contribution to the brief. The brief is already `omit-empty`,
  so an unconfigured source simply produces no section.
- `web-search` absent → still list attendees from the calendar and any local context, but skip the
  external research and the "About the company" section. Say once that attendee research was skipped.
- `outbound-email` absent → **only** when no tool can send mail at all. Prefer a dedicated
  automation sender; otherwise send with the mail connector from the user's own account. See
  `email-delivery.md` for the ordering. Genuinely absent → deliver the brief in chat.
- **Chat-only delivery changes the dedupe guard.** Step 3.5 normally relies on
  searching sent briefs, so with chat-only delivery use the current session instead: if you have
  already produced a brief for this meeting in this session, don't repeat it.

## Load first

- `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` — **read this first.** Where the config lives, what
  to do if it's missing, and how to degrade when a tool isn't configured. Then read the config.
- `${CLAUDE_PLUGIN_ROOT}/shared/scan-sources.md`
- `${CLAUDE_PLUGIN_ROOT}/shared/email-delivery.md`

---

## 1. Find the next meeting

Check the calendar for events starting in the next **~10 to 40 minutes**. On a :20-and-:50 cadence
this window targets the upcoming :30 or :00 meeting plus a buffer. Look at all of the user's
calendars.

- **No meeting in that window** → do nothing further, send no email. Output one line:
  "No upcoming meeting in window — no prep sent." Stop.
- **Multiple** → pick the soonest that qualifies.

When invoked manually, use the meeting the user names, or the next one on their calendar.

## 2. Filter — skip non-work meetings

Skip (send nothing, output one line saying it was skipped and why) anything matching the
**"Meetings to skip in prep"** list in `config.md`. That list typically covers personal events,
training, medical appointments, family, travel, meals, focus blocks, OOO, reminders, and holds with
no attendees — plus any org whose meetings the user doesn't want prepped.

Also apply the calendar attribution rules in `config.md`: a meeting belonging to an org on the skip
list is skipped even if the title doesn't obviously say so.

Ambiguous work-vs-personal: prepare it only if there are external/work attendees or a clear work
agenda. Otherwise skip and say so in one line.

## 3. Build the brief

Gather from every connected tool, memory, and instruction available. Pull what's relevant — don't
force every source. Omit sources with nothing rather than padding. **Do not fabricate.** Disclose
uncertainty explicitly where it matters.

**Calendar event details — capture in full:** title, exact start/end time and timezone, location,
and the **full join details** — video link, dial-in, meeting ID, passcode. Capture the
description/agenda **verbatim** as the organizer wrote it (e.g. a numbered agenda like
"1. Introductions 2. Understand your challenges 3. ..."), plus any attachments. Do not paraphrase
or trim the agenda.

**Attendees — research each one.** List every attendee and identify who they are and their
relationship to the user and their org.

- First cross-reference workspace memory and the people CRM.
- **External** attendees are anyone whose email domain is not in the **Organizations** table in
  `config.md` — a vendor, prospect, partner, or sales rep. For each, run a quick web search for
  role/title, employer, what that company does, and verifiable company facts (scale, funding, recent
  launches, news). Keep it to what genuinely helps the user walk in informed. The email domain is a
  strong employer signal. Cite facts and disclose uncertainty — **never fabricate a title or
  background.** If a person can't be identified, say so plainly ("title not publicly available;
  likely a sales engineer brought in for the demo") rather than inventing detail.
- Flag obvious CRM/tracking aliases (e.g. a "+1" email variant) as not real people.

**Email:** recent inbox threads with the attendees or about the topic, across the accounts in
`config.md`.

**Chat:** recent relevant DMs or channel threads tied to the attendees or topic.

**Meeting notes:** prior meetings with the same attendees or topic — surface last decisions and open
action items where the user is owner/shared/unspecified.

**Issue tracker:** issues tied to the topic or assigned to the user that are relevant.

**Memory & custom instructions:** anything in the workspace context relevant to the people or subject.

### Brief structure

- **Meeting** — title, start/end time, location, full join details (link, meeting ID, passcode)
- **Agenda (from the invite)** — reproduced as written. Omit only if the invite has no agenda.
- **Attendees** — name, then role/title and company for external attendees with a one-line background on who they are and why they matter; internal attendees get a single who/why line. Note any aliases that aren't real people.
- **About the company / external party** — for vendor/prospect/partner meetings: what they do, scale, recent developments relevant to this meeting. Omit for purely internal meetings.
- **Context / why this meeting** — 1–3 lines
- **Recent activity** — relevant email/chat/notes threads, condensed
- **Open items / last decisions** — carried from prior meetings or the issue tracker, if any
- **Suggested talking points / what to walk in knowing** — 2–4 bullets

## 3.5 Dedupe guard — never send the same brief twice

A 30-minute cadence with a ~10–40 minute lookahead means one meeting can fall into two consecutive
runs. Before building or sending, confirm a brief for **this** meeting hasn't already gone out:

1. Compute the exact subject you would send: `Meeting Prep — <meeting title> @ <start time>`,
   using the same title and start-time formatting as step 4.
2. Search the briefing recipient's mailbox for that subject from today — e.g.
   `subject:"Meeting Prep — <meeting title>" newer_than:1d`. The brief is sent *to* that mailbox, so
   a prior brief appears there even though it was sent from the automation sender address.
3. **If a matching message exists, do not send again.** Output one line: "Brief already sent for
   \<title\> @ \<start time\> — skipping duplicate." Stop.
4. Only if no matching brief exists, proceed to step 4.

The subject's start-time component is the dedupe key — stable for a given meeting across runs, so an
exact-subject match means the brief already went out. Match on title **plus** start time; never let
a brief for a different meeting suppress this one.

## 4. Email the brief

Only send when a meeting qualifies **and** the dedupe guard found no prior brief.

Per `${CLAUDE_PLUGIN_ROOT}/shared/email-delivery.md`, with:

| Variable | Value |
|---|---|
| KICKER | `MEETING PREP` |
| HEADLINE | the meeting title |
| Sub-lines | start time and location/link; then full join details (meeting ID / passcode) where present |
| SUBJECT | `Meeting Prep — <meeting title> @ <start time>` |
| Lead callout | **WHAT TO WALK IN KNOWING** — the suggested talking points, as a `<ul>` of 2–4 items |
| Sections | Agenda, Attendees, About the Company, Context, Recent Activity, Open Items / Last Decisions |
| Empty-section mode | **`omit-empty`** — drop any section with no real content rather than rendering an empty bar |
| Plain text | a clean plain-text version of the full prep brief |
| Footer | `— Prep generated <current time> —` |

Section-specific rendering:

- **Agenda** — reproduce as an `<ol>` matching the organizer's numbering and wording.
- **Attendees** — bold each name, follow with role/title and company; background on the same or next line. External attendees get enough to be useful; internal ones stay to a single line.

If the send fails, report the error clearly in chat. Always also output the brief in chat.
