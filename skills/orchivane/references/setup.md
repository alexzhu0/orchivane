# Research, collaboration design and takeover

## New projects: understand the work before choosing chats

Having only an idea, no materials and no other chats is a normal starting point. The current chat owns exploration. Do not begin with an empty role table or ask the user to design the collaboration system. This module covers research, discussion, planning and authorized setup without requiring another skill.

**Use known information before asking decision-changing questions.** Extract the goal, audience, deliverables, success criteria, phase, time/cost constraints and user involvement from accessible sources. Do not chase nonexistent documents or assume dates, budgets or a stack. Ask only a few high-impact questions per round, usually one to three, with recommended options and tradeoffs. Avoid long questionnaires and repeated questions. If the user has no answer, offer labeled assumptions or a bounded exploration and continue independent work; do not promote unknowns to facts.

**Research must inform the collaboration decision.** Read necessary public examples, official documentation or project materials, identifying findings that change delivery steps, required capabilities or acceptance. When research is requested, actually use available retrieval tools and record sources, dates, applicability and gaps. If tools are unavailable, distinguish a research plan from completed research. A vague direction can justify bounded exploration, not endless searches or waiting for every answer. Do not create a research team merely to start researching. Outreach, interviews and paid experiments need their respective authorization.

**Let dependencies determine the structure.** List key deliverables and their order. Identify durable independent context, parallel work, independent acceptance and shared writes. Compare those benefits against transfer, synchronization and waiting costs, then recommend a structure with reasons:

| Observed work | Possible starting structure |
| --- | --- |
| Unclear goal, or a small tightly coupled delivery | Explore or execute in the current chat; no additional chat yet |
| A bounded one-off analysis or verification task | Temporary assistance where permitted; no persistent role required |
| Sustained independent knowledge, parallel delivery or acceptance responsibilities | A controller plus the necessary persistent specialist chats |

These are decision aids, not fixed thresholds or role counts. If the user explicitly wants multiple chats, propose the smallest useful split instead of silently substituting one chat; explain which roles can start later. Do not invent roles from job titles or for apparent completeness.

**Converge on an actionable plan.** Once the first phase's goal, deliverables, key constraints and role-changing questions are clear, produce a short brief and concrete collaboration plan. Do not require an exhaustive domain study. Include facts and sources, answered questions and remaining assumptions; the proposed structure and rationale; each role's deliverable, read/write boundaries, dependencies, acceptance owner and first task; controller closure; and actual changes that would justify adding or merging roles. Mark uncreated roles as proposed, without invented IDs or acceptance status. If staying in one chat, state when to reassess.

**Execute after one confirmation.** Present the structure together with concrete creation and dispatch actions. Execute directly when existing authorization already covers them. If the user only requested research/planning or explicitly deferred creation, deliver the plan and continuation point without starting the roles. Once authorized, use native capabilities to create necessary chats, write the role entry, dispatch initial tasks and inspect substantive acceptance under the dispatch rules. A role list alone does not mean the workflow is running. Minor open questions that do not affect the first phase need not block everything.

Across discussion rounds, persist answered questions, sources, the current plan and next question in the existing brief, or initially in the index's project-brief section below. Saving design records does not mean setup has begun, chats exist or tasks are accepted. Track proposed, creating, created-awaiting-acceptance and accepted states according to actual evidence. Use the current task output directory if no project directory is given; do not require a repository or empty directory tree.

Before creation, define an accessible shared root, each role's write boundaries and the skill version. Check current creation/read/messaging capabilities. Native chats may have different working directories: provide a real absolute shared entry in the first task and have the recipient read it. Verify the version from skill metadata or a release/snapshot manifest, not a spoken label alone.

Creation may start a recipient before returning. Write the proposed record and initial brief first, then register each role immediately when its ready ID returns; do not wait for all roles to finish creation. Only use actual returned IDs. If a recipient sees an outdated proposed status but has a clear task, verifiable authority and accessible inputs with no ownership conflict, it may complete authorized independent preparation and report the registration delay. Pause conflicting writes when a real ownership conflict exists. For an uncertain creation outcome, inspect existing results rather than creating a duplicate to fill the index.

## Existing projects

For initial adoption or a version change, also read [adoption.md](adoption.md): verify the actual source and phase role checks into normal tasks. Inspecting existing TODOs alone does not trigger an upgrade campaign.

Read existing rules, the role index and current changes. When taking over an index from an earlier controller or round, update its header (as-of date, controller, inspected scope) and mark superseded guidance in place before creating roles, since roles read the header first. Refresh the inspected scope at closure. Use chat listings and necessary history to verify actual titles, IDs, responsibilities and status; titles alone cannot disambiguate duplicate names. Reuse roles first and propose new ones only for missing capabilities. Without tools, provide copyable files and briefs and say explicitly that nothing was created or sent.

The current chat is the controller by default; no separate controller chat is required. Respect an existing controller's responsibilities rather than competing for its entry point. If the user only asks which chats exist or what comes next, inspect and answer without dispatching tasks.

Split delivery ownership as needed, such as research, implementation and independent acceptance. Small projects can combine roles; one chat per role or a fixed eight-role structure is not required. Non-engineering work can use document versions, source dates or delivery batches instead of Git fields.

Reuse the index and add concrete role suggestions and briefs. If goals or the basis for the split remain unclear, return to research and discussion. Call chat creation only for an explicit user request; messaging also requires corresponding human authorization. If creation and dispatch are already requested, complete them. When additional authority is genuinely missing, present concrete destinations, messages and actions together and explain the gap, rather than asking an abstract “continue?” question.

## Minimal records

Reuse equivalent project files instead of creating parallel ledgers. During exploration, record the brief and proposed structure; add actual roles during setup. Create change, health-check and handoff records only when needed:

```text
docs/SESSION-MANAGEMENT.md
docs/changes/<change-id>.md
docs/SESSION-HEALTH.md
docs/handoffs/<handoff-id>.md
```

Without a project directory, use the current task output directory; without write tools, deliver text. If internal files are ignored, give other checkouts a stable accessible entry rather than forcing sensitive materials into Git.

Role-index template:

```markdown
# Project collaboration entry
As of: date; controller: actual title/ID/link; inspected scope: ...
Current goal: ...
Effective authorization and limits: original request, allowed actions, budget/stop conditions

## Project brief / collaboration plan
Link an existing brief instead of duplicating it. Record deliverables and success criteria,
sources, answered questions and assumptions, recommended roles and rationale, and next steps.
Distinguish proposed roles from verified acceptance.

| Role | Current chat title / ID | Ownership and delivery | Shared entry / actual directory | Current task and next step |
| --- | --- | --- | --- | --- |

## Current decisions and TODOs
Current conclusions, owners and change links; mark what supersedes old conclusions.

## Important dependencies
Required local materials, frozen inputs, related automation and directories to preserve.

## Handoff relationships
Old chat → successor, actual takeover status and package link.
```

The index has one maintainer, usually the controller. Specialists maintain their own artifacts and receipts; do not let several roles edit the index while the controller owns that write. After checking the existing project instruction file (`AGENTS.md`; for Claude Code see [claude-code.md](claude-code.md)), append an appropriate guide without overwriting its rules:

> For multi-chat collaboration, first read `docs/SESSION-MANAGEMENT.md` to locate your role and current task. The controller consolidates impacts and dispatches under the user's authorization. Specialists deliver authorized work with artifacts, versions, validation and remaining issues. Route cross-role questions to the controller; use the relevant Orchivane modules for handoff and health checks. Existing rules and user authorization remain effective.

## Context recovery

Enter through the current index and change record. Verify completed items and their evidence, then continue unfinished work without replaying the whole plan. Retrieve only necessary history when records are insufficient. Persist decisions, sources and continuation points rather than entire transcripts; the latest message date does not establish source validity.
