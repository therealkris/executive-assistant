# Scheduled Task Registration

> **Using the Cowork desktop app?** Read [`COWORK.md`](COWORK.md) instead. It covers the same thing in
> plain language — phrases you can say, no cron expressions — and includes the one Cowork-specific
> caveat that matters: scheduled tasks only run while the app is open.
>
> This document is the technical reference: cron expressions and task prompts, for Claude Code.

**Claude Code plugins cannot ship scheduled tasks.** Plugin components are skills, agents, hooks,
MCP servers, LSP servers, monitors, commands, and themes — there is no cron or schedule component.[^1]

So the plugin carries the logic and the cron registrations are per-instance. This is a one-time setup
on each machine. After that, every logic change flows through the plugin and the registered tasks
never need touching again.

[^1]: https://docs.claude.com/en/docs/claude-code/plugins-reference

---

## How to register

**The easy path:** run the `setup` skill and say yes when it offers to set up automatic schedules. It
registers only the tasks whose required capabilities you actually have configured, and describes them
in plain terms rather than cron expressions. Everything below is the manual equivalent.

**Only register a task whose required capabilities are configured.** Scheduling `receipt-forward`
with no expense tool, or `meeting-prep` with no calendar, produces a task that runs on a cadence and
reports that it can't do anything — noise on a timer. Check each skill's **Capabilities** block, or
the reference table in `shared/capabilities.md`, before adding its schedule.

To register manually, ask Claude, in a session on the target machine:

> Register the executive-assistant scheduled tasks from
> `<path to plugin>/scheduled-tasks/REGISTER.md`, skipping any whose required capabilities aren't
> configured.

Claude will create each task below. Every prompt is deliberately thin — one line that invokes a
skill. **All logic lives in the plugin, never in the task prompt.** If you find yourself editing a
task prompt, the change belongs in the skill or in your config file instead.

Cron expressions below are examples that work well in practice — adjust hours to your timezone and
working pattern. The scheduler applies jitter automatically.

---

## The tasks

### Inbox triage — business hours

- **cron:** `*/30 7-18 * * 1-5` — every 30 min, 7 AM–7 PM weekdays
- **prompt:** `Run the executive-assistant:inbox-triage skill with window=1h.`

### Inbox triage — weeknights

- **cron:** `0 0,4,20 * * 1-5` — 8 PM, midnight, 4 AM weekdays
- **prompt:** `Run the executive-assistant:inbox-triage skill with window=5h.`

### Inbox triage — weekends

- **cron:** `0 */4 * * 0,6` — every 4 h, Saturday and Sunday
- **prompt:** `Run the executive-assistant:inbox-triage skill with window=5h.`

> One skill, three schedules. The **only** difference is the `window` argument — set it slightly wider
> than the cadence. Idempotency comes from the label check inside the skill, so overlap is safe.

### Morning briefing

- **cron:** `0 7 * * 1-5`
- **prompt:** `Run the executive-assistant:morning-briefing skill.`

### End-of-day wrap

- **cron:** `0 18 * * 1-5`
- **prompt:** `Run the executive-assistant:eod-wrap skill.`

### Weekly review

- **cron:** `0 18 * * 5` — Friday evening
- **prompt:** `Run the executive-assistant:weekly-review skill.`

### Action review (optional)

- **cron:** `0 13 * * 3` — Wednesday midday
- **prompt:** `Run the executive-assistant:action-review skill.`

> Optional by design. `eod-wrap` and `weekly-review` already reconcile and close out the ledger, so
> this is only worth scheduling if you want a mid-week pass. It is most useful invoked on demand.

### Meeting prep

- **cron:** `20,50 6-17 * * 1-5` — :20 and :50 past the hour, weekdays
- **prompt:** `Run the executive-assistant:meeting-prep skill.`

> The :20/:50 offsets pair with the skill's 10–40 minute lookahead so it catches meetings starting on
> the hour and the half hour. Changing one without the other creates blind spots.

### Meeting ingest

- **cron:** `*/30 6-19 * * 1-5`
- **prompt:** `Run the executive-assistant:meeting-ingest skill.`

### Voice profile builder

- **cron:** `0 23 * * *` — nightly
- **prompt:** `Run the executive-assistant:voice-profile skill.`

### Relationship CRM

- **cron:** `0 19 * * 5` — Friday evening, after the weekly review
- **prompt:** `Run the executive-assistant:relationship-cms skill.`

### Receipt forwarding

- **cron:** `0 19 * * *` — daily
- **prompt:** `Run the executive-assistant:receipt-forward skill.`

---

## Migrating from existing standalone tasks

If you already run these as self-contained task prompts, don't delete anything until the plugin path
is proven:

1. Install the plugin and confirm the skills load — `/plugin` should list `executive-assistant`.
2. Invoke one skill manually: "Run the executive-assistant:inbox-triage skill with window=1h."
   Confirm it behaves the same as your current scheduled run.
3. Convert **one** task's prompt to the thin version above. Leave the others alone. Let it run a full
   cycle.
4. Once satisfied, convert the rest.

Keep the old prompts until every task has been converted and has run clean for a few days. They are
your only rollback.

## Before you register

Confirm the connectors named in your config file are authorized on this machine — mail, calendar,
chat, issue tracker, notes source, and outbound sender. A task whose connector is missing fails at
run time, not at registration. Unauthorized connectors need an interactive OAuth flow, which a
scheduled run cannot perform.

Also confirm your config file exists — `setup` writes it, and `shared/capabilities.md` lists the
locations skills look in. Skills that can't find it will tell you to run `setup` and stop, which is
the intended behavior, but it means a scheduled run produces nothing until you do.
