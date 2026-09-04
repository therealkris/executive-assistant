---
name: inbox-triage
description: Triage the user's work email inbox — classify each new message as Archive/Delete/Reply, apply labels, and draft in-thread replies in their voice. Use when the user says "triage my inbox", "check my email", "process my inbox", "what do I need to reply to", or when a scheduled triage run fires. Accepts a lookback window argument (e.g. window=1h for 30-minute cadence, window=5h for 4-hour cadence).
---

# Inbox Triage

Triage the user's work email inbox: classify, label, and draft. Each run starts fresh with no memory
of prior runs — follow these instructions exactly.

**Argument:** `window` — the mail lookback. Defaults to `1h`. Set it slightly wider than the run
cadence so nothing falls between runs:

| Cadence | window |
|---|---|
| Every 30 min | `1h` |
| Every 4 hours | `5h` |

Idempotency comes from the label check in *Scope*, not from a tight window — overlap is safe.

## Capabilities

**Required:** `mail`
**Optional:** `mail-draft`, `voice-profile`, `people-crm`

- `mail` absent → do not run. Say that no email account is configured and that `setup` can add one.
- `mail-draft` absent → still classify and label, but create no drafts. Say so in the summary.
- `voice-profile` absent → draft in a neutral-professional tone and note it, since the drafts will
  read less like the user than they eventually should.
- `people-crm` absent → skip the sender lookup; use a neutral-professional tone.

## Load first

1. `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` — **read this first.** It says where the config
   lives, what to do if it's missing, and how to handle tools the user hasn't configured. Then read
   the config it points to for accounts, connector rules, paths, and conventions.
2. `${CLAUDE_PLUGIN_ROOT}/shared/scan-sources.md` — mail query discipline.
3. Any workspace-level instruction files named in the config — routing, voice, and contact rules.
4. The voice profile (path in `config.md`) — read before drafting any reply. Match its tone exactly.
   No filler.
5. Sender and relationship context from the people CRM folder (path in `config.md`). Use whatever is
   found to judge tone, tier, and active-thread context. If nothing is found, use a
   neutral-professional tone.

## Account

Operate **only** on the account the config designates for triage — by default the **primary work**
account. Do not touch any other account.

Follow the read/label vs. draft connector split in `config.md`. It matters: some connectors' draft
tools don't bind to an existing thread, producing detached standalone drafts instead of replies.

## Scope per run

Process only **new, unprocessed** inbox mail:

- Scope to the inbox and `newer_than:<window>`.
- Skip anything already tagged **"To Archive"**, **"To Delete"**, or already carrying a topic label
  — so the same email is never handled twice.
- Inbox only. Never surface or act on archived mail.

## Classify — exactly one action per email

**ARCHIVE** — informational, no response or follow-up needed:

- Automated notifications (cloud provider, source control, monitoring) needing no action
- FYI threads where the user is CC'd and no action is expected of them
- Meeting confirmations / calendar invites already handled
- Receipts or invoices needing no action
- Read receipts, delivery confirmations
- Newsletters and digests the user actually reads (not spam)

**DELETE** — no value:

- Marketing / promotional from companies with no existing relationship
- Cold outreach and solicitations — **but** if the sender could plausibly be relevant, ARCHIVE
  instead. When in doubt, ARCHIVE, never DELETE.
- Social media notifications
- Spam

**REPLY** — the user's response is needed:

- A direct question addressed to them
- A request for information, a decision, or an approval
- A follow-up on an open thread where their input is the next step
- A scheduling request needing confirmation
- A vendor or partner asking for something

### Exception — skip drafting if the user already replied

Before drafting, check the thread's most recent message. If the latest message is **from the user
and postdates the message being triaged** — meaning they already replied, whether through this flow,
manually, or any other channel — do **not** create another draft.

Treat it as handled: apply the relevant topic label(s) only.

## Handle each action

| Action | What to do |
|---|---|
| ARCHIVE | Apply label **"To Archive"** plus relevant topic label(s) from the existing label list; create a sensible new topic label if none fits. Do **not** actually archive or remove from inbox — label only, so the user reviews. |
| DELETE | Apply label **"To Delete"**. Do **not** actually delete — label only. |
| REPLY | Run the drafting flow below. Also apply relevant topic label(s), creating one if none fits. |

## Reply drafting flow

1. Look up the sender in the people CRM to understand tone, tier, and active-thread context.
2. Read the **full thread**, not just the latest message, with analysis enabled. Check the last
   sender and whose court the ball is in — if the last message is already from the user and
   postdates the triaged message, stop here: apply topic label(s) only and do not draft.
3. Draft in the matching voice from the voice profile. Match tone exactly. No filler.
4. Create the draft with the drafting connector from `config.md`, passing:
   - the triage account explicitly
   - recipient (and CC where applicable)
   - subject = `"Re: <original subject>"`
   - the thread ID of the original thread
   - the in-reply-to header set to the latest message's RFC Message-ID

   Both the thread ID and the in-reply-to header are required for the draft to nest in-thread.
   Do not send.

## Constraints

- **This skill is the complete implementation. Do not delegate to any other triage skill.** Other
  installed skills may advertise nearly identical trigger phrases while carrying different account
  scope, label taxonomy, and drafting rules. If another triage skill activates alongside this one,
  this one governs.
- **Never send email.** Drafts and labels only.
- **Never delete or archive directly.** Labeling only.
- Do not fabricate. If a sender or thread can't be verified, label conservatively and skip the draft.
- Never draft a reply to a message the user has already answered.

## Output

Brief summary: counts per action (Archive / Delete / Reply), the subjects and senders handled, and
which drafts were created — noting any REPLY-classified threads skipped because the user already
replied. If nothing new arrived: **"No new inbox mail this run."** Keep it concise.
