---
name: voice-profile
description: Incrementally refines the user's voice profile by analyzing their sent email, chat messages, and call transcripts so future drafts sound authentically like them. Use when the user asks to update or rebuild their voice profile, says drafts don't sound like them, or when the nightly voice-profile run fires.
---

# Voice Profile Builder

Maintain the user's **voice profile** — a living model of how they write and speak, used so future
drafts (emails, chat messages, documents) sound authentically like them.

Run **incrementally**: refine and extend what's already there. **Never wipe prior learning.**

## Capabilities

**Required:** at least one of `mail`, `chat`, `meeting-notes`

- **All three absent** → do not run. There is no material to learn a voice from. Say so plainly.
- Any individual source absent → skip it. A voice profile built from email alone is still useful;
  note in the changelog line which sources were available so later runs can fill the gaps.
- This skill is what makes `voice-profile` available to the other skills. If the config marks
  `voice-profile` as `not configured` because no file path was set, say that a location is needed
  before the profile can be stored, and point at `setup`.

## Load first

- `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` — **read this first.** Where the config lives, what
  to do if it's missing, and how to degrade when a tool isn't configured. Then read the config for
  accounts and paths.

The file you maintain is the voice profile at the path given in the config.

**Read it first.** Note `last_sources_through` in the frontmatter — that's how far the profile has
already analyzed. If empty (first run), default to the **last 14 days** for email and chat, and
analyze **all** existing call transcripts.

---

## Step 1 — Gather what's new

Pull only material **authored by the user** since `last_sources_through` (or the default window).

- **Sent email, per account** — for each account in the config, search sent mail for the window.
  Read a representative sample (~15–30 messages per account). Focus on messages the user actually
  wrote; skip pure forwards and one-liners like "thanks."
- **Chat** — messages the user sent in the window. If the search returns nothing, record "no relevant
  messages found." Do not claim the connector is unavailable.
- **Call transcripts** — new files in the transcripts folder dated after `last_sources_through`. In
  each, focus **only on the user's own spoken lines** (their name/turns), not other speakers.

If a source has nothing new, skip it — don't force it.

## Step 2 — Update the profile

Abstract patterns from the real material and **fold them into the existing sections** — don't just
append. Update:

- **Core Voice** — sentence length, signature phrases and tics, vocabulary, punctuation and
  formatting habits, humor/warmth markers.
- **Voice by Context** — refine the right block(s): external work email, internal work email,
  personal email, chat, spoken/meetings. Capture tone, openers, closers and sign-offs, formality.
- **Sign-offs & Greetings table** — fill with what's actually observed.
- **Do / Don't checklist** — concrete, actionable rules a drafter should follow to match the voice.
- **Representative Snippets** — a small rotating set (~3 per context) of short, lightly-anonymized
  real examples. **Cap each context at 3** — drop the oldest when adding a newer, better one. Remove
  names, dollar figures, and confidential deal or legal specifics; keep the phrasing and structure.

Be evidence-based and concise. If the data for a context is thin, leave it honest
("limited data so far") rather than inventing patterns. Apply the config's capitalization rules.

## Step 3 — Bookkeeping

- Update frontmatter: `last_updated` = today, `last_sources_through` = today, `status: active`.
- Append **one** line to the Changelog: `YYYY-MM-DD — sources reviewed (counts), what changed`.
- **Do not write to auto-memory** — memory is user-triggered only. Only this markdown file changes.

## Output

Keep it quiet — this is automated maintenance. After updating, output 2–3 lines: which sources you
reviewed, counts, and the most notable voice insight added.
