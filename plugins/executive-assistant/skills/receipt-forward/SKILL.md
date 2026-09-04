---
name: receipt-forward
description: Forwards new credit-card receipts above a threshold from the user's work email to their expense tool, excluding AP/invoice billing routed to accounting, and labels the originals "submitted". Use when the user asks to forward receipts, submit expenses, "send my receipts to expenses", or when the daily receipt-forwarding run fires.
---

# Receipt Forwarding

Forward newly-received receipts from the user's primary work account to their expense tool's intake
address.

On a daily cadence, process only email received in the **last 24 hours**.

## Capabilities

**Required:** `mail`, `expense-tool`

- Either absent → do not run. Say which is missing and point at `setup`.
- The config's **Expense forwarding** section must supply an intake address and a minimum amount. Without
  those, treat `expense-tool` as absent and forward nothing.
- **Exclusion list vs. strict mode.** The payment-method filter in step 2 needs one of two things to
  distinguish a card charge from an invoice the finance team pays:
  - **An AP/accounting exclusion list** — the normal case. Skip anything addressed to those roles.
  - **`strict-confirmation` set** — the fallback when the user didn't know their AP addresses. Forward
    **only** on positive evidence that a card was already charged: a card's last four digits, a
    transaction or charge ID, or explicit wording like "payment successful" / "your card was charged."
    Anything that merely reads like an invoice is skipped. This under-forwards on purpose.

  If **neither** is present, treat `expense-tool` as absent and forward nothing. Forwarding an
  AP-billed invoice onto someone's personal expense report is worse than forwarding nothing.

## Load first

- `${CLAUDE_PLUGIN_ROOT}/scripts/receipt_to_pdf.py` — bundled receipt-to-PDF generator used by
  step 5b. Requires `python3` only; no third-party packages.
- `${CLAUDE_PLUGIN_ROOT}/shared/capabilities.md` — **read this first.** Where the config lives and
  how to degrade. Then read the config for accounts, expense intake address, amount threshold, group
  aliases, AP addresses, and known exclusions.

**Account:** use the mail tools with the **primary work** account for all reads, downloads, sends,
and label updates. Confirm it's connected first if the connector supports an account listing call.

**Label:** resolve the label "submitted" once per run via a get-or-create call to get its ID —
needed for step 6.

---

## Step 1 — Find candidates

Search the primary work **mailbox** for receipts and invoices from the last 24 hours.

**Do not restrict by `in:inbox`.** This skill is an explicit exception to the config's global
"every Gmail search must include `in:inbox`" rule. Vendor receipts are routinely auto-filtered,
auto-archived, or labeled straight past the inbox by Gmail filters, so an `in:inbox` scope silently
drops real receipts. Recurring SaaS subscription receipts are the usual casualty: a filter set up
months ago to keep them out of the inbox also hides them from this skill. Scope by excluding trash
and spam instead, and let the label check in step 4 prevent reprocessing.

**Do not restrict by `To:` header.** Vendor receipts often arrive with a blank, BCC'd, or
non-matching `To:` field — some enterprise billing receipts show an empty `To:` header entirely — so
a `to:` filter silently misses real receipts. The search is already scoped to one account, so
anything delivered to it is fair game for review.

```
(receipt OR invoice OR "your receipt" OR "billing receipt" OR "payment receipt" OR "payment received" OR "payment has been processed" OR "processed payment" OR "thank you for your payment" OR "subscription payment" OR "subscription renewal") newer_than:1d -in:trash -in:spam
```

Use a result limit of at least 50. Then read each candidate to confirm it is genuinely a receipt or
paid invoice — **check the body and attachment, not just the `To:` header.**

**If the read returns an empty or near-empty body,** the message is almost certainly HTML-only and
the body extraction failed. Do not treat that as "not a receipt." Re-read the message (raw/full
format if the connector offers one), or fall back to the attachment and the subject line. If the
body still cannot be recovered, forward it and note "body unreadable — verify amount" rather than
dropping it silently.

Informational only, not a filter: receipts sent to any **group inbox alias** in the config arrive in
this inbox, often tagged with the group name.

## Step 2 — Payment method filter (credit card charges only)

The expense tool should only receive items representing an **actual credit card charge.** Invoices
routed to accounting for manual/AP payment (wire, ACH, check, or manually-keyed card entry processed
by the finance team) do **not** belong on the user's expense report, even if the email is titled
"invoice" or "receipt."

**FORWARD — credit card payment signals:**

- Explicit confirmation a card was charged: "your card was charged", "payment method: •••• 1234",
  "charged to [card] ending in ____", "auto-renewal charged", "payment successful", or
  "payment received" tied to a card or digital-wallet transaction.
- Standard SaaS subscription auto-billing receipts where the vendor confirms a charge **already
  occurred** against a card on file.
- **Past-tense confirmation of a completed payment on a recurring subscription counts, even with no
  card last four.** Wording like "we have successfully processed payment for your recurring
  <plan> subscription", "thank you for your payment", or "your subscription has renewed" is
  sufficient evidence of a card charge on a self-serve SaaS plan. Most vendors never print the card
  digits. Do not hold out for a last four that will never appear.
- **A Stripe-style invoice reference on a completed-payment receipt is a transaction ID, not an AP
  invoice.** An `Invoice ID: in_...` (or `Receipt number`, `ch_...`, `pi_...`) alongside past-tense
  payment wording is the charge reference — forward it. Only the *combination* of an invoice
  reference with a **request for future payment** (remit, due by, Net 30, "amount due") makes it AP
  billing.
- A representative self-serve card-billed vendor: a design or collaboration SaaS sending a monthly
  "Receipt for subscription payment <date>" for a team plan, carrying a Stripe `in_` invoice ID and
  no card digits — forward these. Add your own vendors to the config's **known exclusions** only
  when they turn out to be AP-billed.

**DO NOT FORWARD — AP/invoice billing signals** (exclude even if worded like a receipt):

- Emails addressed primarily to any **accounting / AP address** in the config — even if the user is
  CC'd — or that say the invoice was "sent to accounting," "for AP processing," "remit payment," or
  "Net 30," or "due by [date]" without confirming a card was already charged.
- Vendor invoices requesting **future** payment rather than confirming a charge that already happened.
- Any vendor named in the config's **known exclusions**. Treat similarly-structured vendor invoices
  the same way.

**When `strict-confirmation` is set** (no AP exclusion list available), invert the default: forward
only on positive evidence of a completed card charge — card last four, a transaction/charge ID, or
explicit "payment successful" / "your card was charged" wording. Absent that evidence, skip and note
it as "skipped — no confirmed card charge." Under-forwarding is the intended behavior here; the user
chose this mode precisely because the exclusion list wasn't knowable.

If genuinely ambiguous — some vendors word auto-charged receipts like invoices — read the full body
and attachment for hard confirmation (card last 4, "payment succeeded," a transaction/charge ID).
**If you can't confirm an actual charge, exclude it** and note it in the summary as "excluded —
appears to be AP invoice, not a card charge" rather than guessing.

## Step 3 — Amount threshold

Determine each item's total from the email body. **Skip anything below the minimum amount in the
config.**

If the amount genuinely cannot be determined from the body, forward it anyway and note it as
"amount undetermined" in the summary.

## Step 4 — Skip already-forwarded

Search sent mail for the expense intake address over the last 2 days. Skip any candidate whose
receipt/invoice already appears there — match on vendor plus receipt/invoice number or subject.

As a second check, skip anything already carrying the "submitted" label.

## Step 5 — Forward

Forward each qualifying item **from the primary work account** to the expense intake address. The
config lists which sender addresses the expense tool accepts; forwarding from the primary work
account covers group-alias receipts too when both are registered.

**Every forward must carry exactly one PDF.** The expense tool reads attachments, not forwarded
email text — a text-only forward lands as an unparsed expense that has to be keyed in by hand. So
each qualifying item gets one PDF and only one: the vendor's receipt PDF when there is one,
otherwise a generated one.

### 5a — Vendor supplied PDF attachments

Download and attach **exactly one** PDF: the **receipt**, never the invoice.

- **Two attachments (invoice + receipt)** — the common Stripe-hosted pattern: the vendor sends
  `Invoice-<invoice number>.pdf` and `Receipt-<receipt number>.pdf` on the same email. Attach
  **only** the receipt. Two attachments means two expenses in the expense tool, and the invoice copy
  is the wrong one to keep.
- **Choosing between them:** prefer the attachment whose filename contains `receipt` and does not
  contain `invoice`. If filenames are ambiguous, open both and keep the one that states an amount
  **paid** (`Amount paid`, `Paid <date>`, `Receipt number`) over the one stating an amount **due**.
- **One attachment only:** attach it, whichever it is.
- Never attach more than one PDF per forward, and never attach a logo, banner, or other inline
  image the connector reports as an attachment.

### 5b — No PDF attachment: generate one

Receipts that live only in the email body — recurring SaaS subscription receipts are the standing
example — must be converted to a PDF before forwarding. Transcribing the details into the body is
**not** sufficient; the expense tool does not read it.

Use the bundled generator (stdlib Python, no dependencies):

```bash
printf '%s\n' \
  "Vendor: Acme SaaS" \
  "Amount: $120.00 USD" \
  "Date: Aug 25, 2026" \
  "Billing period: Aug 25, 2026 - Sep 25, 2026" \
  "Invoice ID: in_00000000000000" \
  "Plan: Team (monthly)" \
  "Payment: card on file charged by vendor" \
  "Source: email receipt from billing@acme-saas.example, no PDF attachment" \
| python3 "${CLAUDE_PLUGIN_ROOT}/scripts/receipt_to_pdf.py" \
    --out "/tmp/receipt-acme-saas-2026-08-25.pdf" \
    --title "Acme SaaS - Receipt (Aug 25, 2026)"
```

Rules for the generated PDF:

- Include, in this order and only where the email actually states them: Vendor, Amount, Date,
  billing period, invoice/receipt number, plan/description, payment method (card last four if
  present), and a `Source:` line naming the sender address. **Never invent a field** — omit what the
  email does not state.
- Filename: `receipt-<vendor>-<YYYY-MM-DD>.pdf`, lowercase, written to a temp path — never into the
  user's folders.
- Title: `<Vendor> - Receipt (<date>)`.
- If the generator fails or `python3` is unavailable, **still forward** with the details transcribed
  into the body, and flag it in the summary as "forwarded without PDF — needs manual attachment."
  Do not silently skip.

### 5c — Message shape

- **Subject:** `Fwd: <original subject>`.
- **Body:** a brief forwarded header (From, Date, Subject) plus the transcribed amount/date/number
  details — this stays useful for human review even though the PDF is what gets parsed.
- **Attachment:** exactly one PDF, per 5a or 5b.

## Step 6 — Label the original "submitted"

Immediately after each successful forward, apply the label to the original message using the label ID
resolved at the start of the run.

This flags it visually in the inbox and prevents reconsideration on a future run.
**Only label messages actually forwarded this run** — never label skipped or excluded items.

## Step 7 — Report

Concise summary: a table of what was forwarded (vendor, amount, date, and whether the PDF was the
vendor's own or generated) noting each was labeled "submitted," and a list of what was skipped and
why (below threshold, already forwarded, not a receipt, excluded as AP/invoice billing). Flag any items where the amount could not be determined.

## Constraints

- **Do not send anything to addresses other than the expense intake address.**
- **Do not modify or delete any email** other than applying the "submitted" label to originals
  forwarded this run.
