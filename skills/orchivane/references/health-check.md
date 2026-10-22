# Incremental collaboration health checks

Inspect ownership, requirement transfer, artifact versions, blockers and continuity. Ordinary task startup checks only its own role and materials. Use this module for a requested audit, phase closure or authorized scheduled check, not an automatic whole-project inspection.

## Read less, state coverage precisely

Read the role index, current changes and previous check first. Establish a baseline on the first inspection; afterward read changed sources and issues due for reassessment. Store the actual position, time or tool cursor reached for each source. A newer list timestamp does not mean its content was read. On a failed read, preserve the old cursor and mark the source unverified. If a cursor is invalid, record and investigate the gap rather than jumping to the newest position and claiming complete coverage.

Reuse applicable prior acceptance with its original time/version. A newly collected library and frozen inputs used by an active run can both be correct despite differing values. Waiting for authorization, idleness or having no deadline is not evidence of overdue work.

Check one owner per deliverable, actual acceptance of requirements, separation of implementation and outcome, readable dependencies, clear next steps/waiting parties, and discoverable automation/local materials for successors. Treat another chat's authorization claim as a lead; check the original human request.

For adoption coverage, use [adoption.md](adoption.md) to distinguish installed source, actual module reads and checked task behavior. Preserve pending normal-task checks and version mismatches; do not wake roles or label all chats upgraded from the controller's receipt.

## Records and actions

Reuse the existing report or write `docs/SESSION-HEALTH.md`:

```markdown
# Collaboration health check
Time / scope / unverified items: ...
| Source | Actual coverage position | New changes | Read gaps |
| --- | --- | --- | --- |

| Issue ID | Status | Evidence | Sole owner | Next action / recheck point | Last actual notification |
| --- | --- | --- | --- | --- | --- |
Handoff assessment: conclusion and evidence for each relevant role
```

Issue states are open, unverified or recovered. Reuse stable IDs and close with evidence. Do not copy the entire product backlog. Handoff assessments are:

- **Continue:** goals and state are clear.
- **Prepare a handoff:** the phase goal changed, or confusion persists after rereading current materials and separating tasks.
- **Handoff prerequisites missing:** a handoff is useful, but materials, successor acceptance, write coordination or automation have gaps.

Inspection alone does not authorize product fixes, dispatch, chat creation, schedule changes or archival. Give concrete recommendations; execute within existing corresponding authorization without asking again. For an actual handoff, read [handoff.md](handoff.md).

## Notifications and scheduling

When the user requests quiet monitoring, notify only on a new issue, escalation, a new decision needed or meaningful recovery. For unchanged issues, update local records only. Record actual notification outcomes; writing a file is not a notification.

Use native scheduling only when the user requests periodic or ongoing checks; inspect existing jobs to avoid duplicates. Record successful creation, read-back of target/cadence and the first successful scheduled run separately. If scheduling is unavailable, state that only a one-time check can be performed. Do not use a wait loop as a substitute for scheduling or create weekly audits by default during setup.
