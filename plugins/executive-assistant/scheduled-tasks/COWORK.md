# Setting these up to run automatically (Cowork)

You don't have to remember to ask for a briefing. Each of these skills can run on a schedule — a
morning briefing waiting for you at 7, an end-of-day wrap at 6, inbox triage every half hour.

**You don't need to know anything technical.** Just say what you want in plain words. Claude sets it
up. Everything below is copy-and-paste ready.

---

## Two things to know first

**1. Schedules only run while the Cowork app is open.** If your laptop is closed at 7am, the morning
briefing doesn't run at 7am — it runs the next time you open the app. That's usually fine (you get it
when you sit down), but it's the one surprise worth knowing about up front. If you want something to
land at a guaranteed time, this isn't the tool for it.

**2. Each run starts fresh.** A scheduled task has no memory of your conversations. It reads your
settings and does its job. That's why setup wrote your configuration to a file — so every scheduled
run has the same context you do.

---

## Just say one of these

Pick the ones you want. You can add more later, change the times, or turn any of them off.

**Morning briefing** — your day, waiting for you:

> Every weekday at 7am, run my morning briefing.

**End-of-day wrap** — what's unfinished, what tomorrow looks like:

> Every weekday at 6pm, run my end-of-day wrap.

**Inbox triage** — sorts new mail and drafts replies as it arrives:

> Every 30 minutes on weekdays between 7am and 7pm, triage my inbox with a 1 hour window.

Off-hours, less often:

> Every 4 hours on weeknights and weekends, triage my inbox with a 5 hour window.

**Meeting prep** — a brief before each meeting:

> At 20 and 50 minutes past the hour, weekdays 6am to 6pm, run my meeting prep.

*(Those odd times are deliberate — they pair with how far ahead the skill looks, so it catches
meetings starting on the hour and the half hour. Changing one without the other creates gaps.)*

**Action items** — what's still open, and a chance to close things out. The end-of-day wrap and
weekly review already do this, so schedule it separately only if you want a mid-week pass:

> Every Wednesday at 1pm, show me my open action items.

**Weekly review** — a Friday summary:

> Every Friday at 6pm, run my weekly review.

**Meeting notes** — files notes as meetings finish:

> Every 30 minutes on weekdays between 6am and 8pm, ingest my meeting notes.

**Writing voice** — learns how you write, overnight:

> Every night at 11pm, update my voice profile.

**Contacts** — keeps your people notes current:

> Every Friday at 7pm, refresh my contacts.

**Receipt forwarding** — sends receipts to your expense tool:

> Every day at 7pm, forward my receipts.

---

## Only schedule what you set up

If you didn't configure a feature, don't schedule it. A scheduled task for something unconfigured
runs on a timer and reports that it can't do anything — noise on a schedule.

If you're unsure what you have, just ask:

> What did I set up, and what could I schedule?

---

## Changing or stopping them

All plain language, no syntax:

> What scheduled tasks do I have?

> Change my morning briefing to 6:30am.

> Pause my receipt forwarding.

> Stop running the weekly review.

---

## A reasonable starting point

If you'd rather not choose, this is a sensible default set — enough to be useful, not enough to be
noisy:

> Set up my morning briefing for weekdays at 7am, my end-of-day wrap for weekdays at 6pm, and inbox
> triage every 30 minutes during weekday business hours.

Add meeting prep once you trust the briefings. Leave the rest until you miss them.

---

## Notes

- Times are **your local time**. No timezone conversion needed.
- Recurring runs are offset by a few minutes to spread load, so a 7am task may arrive at 7:03.
- You'll get a notification when a task finishes. Ask to turn that off if it's noise.
- Tasks are stored on your own computer, one folder per task, under your Claude documents folder.
- Re-run `setup` any time — it can add schedules for you too, and only offers the ones your
  configuration actually supports.
