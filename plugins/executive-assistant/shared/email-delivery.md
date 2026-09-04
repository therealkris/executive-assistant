# Email Delivery — Send Mechanics + HTML Spec

Shared by `morning-briefing`, `eod-wrap`, `meeting-prep`, and `relationship-cms`.
Each caller supplies four values: **KICKER**, **HEADLINE**, **SUBJECT**, and **SECTIONS**.

---

## Send mechanics

**Pick a sending path in this order. Use the first that works.**

1. **Dedicated automation sender** — if the config names an *outbound automation sender* (a service
   like AgentMail), send from that. Preferred: briefings arrive from a distinct address, so they're
   filterable and never mixed into the user's own sent mail.
2. **The mail connector's send tool** — if no automation sender is configured but the mail connector
   can send (e.g. a Gmail `send_email` tool), use it, sending **from the user's own primary work
   account to the briefing recipient**. This is the common case and works fine. The only cost is that
   briefings appear in the user's Sent folder.
3. **Neither can send** → only now treat `outbound-email` as absent. Deliver the full content in chat
   and note it once: "Delivered in chat — no way to send mail is configured."

**Do not skip email delivery merely because no dedicated sender exists.** If mail is connected at all,
it can almost certainly send. Falling straight to chat when a working send tool was available is the
failure mode this ordering exists to prevent.

If the tool isn't loaded, find it via tool search before concluding it's unavailable.

| Field | Value |
|---|---|
| sender | the **outbound automation sender** from the config if set; otherwise the **primary work account** |
| recipient | the **briefing recipient** from the config; default to the primary work account |
| `subject` | caller-supplied SUBJECT |
| `text` | clean plain-text version of the full content, as a readable fallback |
| `html` | formatted version per the spec below |

When falling back to path 2, say so once in the chat output — "Sent from your own account; no
dedicated automation sender configured" — so the user knows why it's in their Sent folder and can add
a dedicated sender later if they'd rather.

Send **even on quiet days** where sections report "nothing needing attention" — except where
the calling skill defines an explicit skip condition (e.g. `meeting-prep` sends nothing when no
meeting qualifies, and nothing when its dedupe guard fires).

If the send fails, report the error clearly in the chat output. Always also output the content in chat.

---

## HTML spec

Email-client-safe: **inline CSS only.** No `<style>` blocks, no external CSS, no JavaScript.
Build the `html` body as a self-contained fragment. Light theme throughout.

### Wrapper

```
max-width:640px; margin:0 auto;
font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
color:#1a1a1a; line-height:1.5; font-size:15px;
```

### Title block

- **KICKER** — small, uppercase, letter-spaced, `#6b7280`
- **HEADLINE** — large and bold, ~22px, `#111827`
- Optional sub-lines (times, locations, join details) in `#6b7280`
- Close the block: `border-bottom:2px solid #111827; padding-bottom:12px; margin-bottom:20px;`

### Lead callout box

The first section is always a highlighted callout — the priority snapshot, or the "what to walk in
knowing" points.

```
background:#f0f7f4; border-left:4px solid #16a34a; border-radius:6px;
padding:14px 16px; margin-bottom:24px;
```

Header in bold uppercase, `#15803d`, ~12px, letter-spaced. Bold the lead phrase of each item.
Use `<ol>` for a ranked snapshot, `<ul>` for unranked points.

### Section headers

Every subsequent section header renders as a styled bar:

```
background:#f3f4f6; border-radius:5px; padding:8px 12px; margin:22px 0 10px;
font-size:12px; font-weight:700; letter-spacing:.05em; text-transform:uppercase; color:#374151;
```

**Empty-section handling is set by the calling skill.** Two modes — the caller must name one:

- **`report-nothing`** (briefings): render the section and state its "nothing" status in normal text
  — "no items needing attention", "no tracker issues due today", "no inbox mail for this account".
  Explicit negative reporting is the point; a missing section is indistinguishable from a failed scan.
- **`omit-empty`** (prep briefs): drop the section entirely rather than rendering an empty bar.

### Section bodies

- Lists: `<ul style="margin:6px 0 6px 0; padding-left:20px;">` with `<li style="margin-bottom:6px;">`
- Bold key labels: sender names, issue IDs (e.g. `ENG-602`), meeting titles, owners, due dates, company names
- Overdue / urgent / blocking / time-sensitive flags in red: `color:#dc2626; font-weight:700;`
- Muted italic asides (e.g. "why it matters" tags): `<span style="color:#6b7280; font-style:italic;">`
- Source citations: simple `<a>` in `#2563eb`
- Sub-labels within a section: bold, ~13px, `#374151`
- Email addresses and meeting links: plain styled text or simple `<a>` tags. Do not produce noisy mailto markup.

### Amber callout (action required)

For blocks that ask the user a direct question or require their input:

```
background:#fffbeb; border-left:4px solid #d97706; border-radius:6px;
padding:12px 14px; margin:12px 0;
```

Label in bold.

### Footer

Centered, muted, caller-supplied text (e.g. `— End of briefing —`, `— Prep generated <time> —`):

```
color:#9ca3af; font-size:12px; text-align:center; margin-top:24px;
border-top:1px solid #e5e7eb; padding-top:12px;
```

---

## Hard rule

**Do not fabricate content to fill the template.** A section with nothing in it either states its
"nothing" status in normal text or is omitted entirely — per the mode the calling skill declared
above. Never invent content to avoid an empty section.
