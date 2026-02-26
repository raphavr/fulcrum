---
name: compound-learning
description: Use when the user invokes /compound, says "capture learnings", "what did we learn", or when suggesting post-cycle knowledge capture after completing a development branch
---

# Compound Learning

## Overview

Compound learning captures knowledge from completed development cycles — what worked, what didn't, patterns discovered, gotchas encountered — and feeds it back into project configuration to improve future cycles. It is optional, engineer-driven, and never forced.

## When to Use

- User explicitly invokes `/compound`
- User says "capture learnings", "what did we learn", "review what happened"
- After finishing a development branch (suggest it, but don't force it)

**When NOT to use:**
- Mid-cycle (wait until the work is complete or at a natural stopping point)
- If the cycle was trivial (a one-line fix doesn't need a learning capture)
- If the engineer declines — respect that and move on

## Core Principles

- **Optional** — Engineer chooses when to run, never forced
- **Non-nagging** — If no notable learnings in a cycle, say so and move on
- **Engineer approval** — Every learning must be approved before applying
- **Incremental** — One or two learnings per cycle is fine, don't force quantity
- **Avoid bloat** — Learnings should condense over time, not accumulate forever

## Phase 1: Gather Cycle Data

Identify the most recently completed cycle by examining:

1. **Git history** — Check `git log` for recent commits on the current branch. What was the scope of work?

2. **Spec document** — Look in `docs/specs/` for a spec associated with this work. If found, it provides the original intent and requirements.

3. **Plan document** — Check if a plan was created (/spec or /write-plan output). This shows the intended approach.

4. **Files changed** — Run `git diff --stat` against the base branch to see what was actually modified.

5. **Session notes** — Check `docs/session-notes/` for debrief files left by subagent implementers. These capture gotchas, false starts, and decisions that never appear in commits. Read all notes from this cycle (match by task name or recency). These are the richest source of learnings — don't skip them.

6. **Cycle context summary:**
   - What was the goal? (from spec, commits, or ask the engineer)
   - What was the estimated complexity?
   - What was actually implemented?
   - Were there surprises or deviations from the plan?

Present the cycle summary to the engineer for confirmation before proceeding:

> I found the following cycle: [summary]. Is this the work you want to capture learnings from?

## Phase 2: Identify Learnings

Analyze the cycle for notable learnings in these categories:

| Category | What to look for |
|----------|-----------------|
| **Patterns** | Recurring code patterns or architectural decisions that worked well |
| **Gotchas** | Problems encountered and how they were resolved |
| **Tools** | Libraries, frameworks, or tools that were particularly useful or problematic |
| **Process** | Aspects of the development workflow that helped or hindered |
| **Project-specific** | Conventions or constraints specific to this project |
| **False starts** | Approaches tried and abandoned (and why) |

For each proposed learning, provide:

- **Category** — Which of the above categories
- **Description** — What was learned (one or two sentences)
- **Context** — When does this apply? When is it NOT relevant?
- **Example** — Concrete instance from the cycle that demonstrates this

Present proposed learnings one at a time. For each one, the engineer can:
- **Approve** — Learning will be recorded
- **Modify** — Edit the description or context before recording
- **Reject** — Skip this learning, no hard feelings
- **Stop** — Done reviewing learnings, apply what's been approved so far

If no notable learnings are found, say so honestly:

> This cycle was clean — no notable learnings to capture. The existing patterns and standards worked well.

## Phase 3: Apply Learnings

For each approved learning:

### 1. Create a learning document

Save to `docs/learnings/YYYY-MM-DD-topic.md`:

```markdown
# Learning: [Topic]

**Date:** YYYY-MM-DD
**Category:** Pattern | Gotcha | Tool | Process | Project-specific
**Cycle:** [Related spec or feature description]

## Description
[What was learned]

## Context
[When does this apply? When is it not relevant?]

## Example
[Concrete instance from the cycle that demonstrates this learning]

## Applied To
- [x] `docs/learnings/` — This document
- [ ] `CLAUDE.md` — [pending or description of what was added]
- [ ] `.claude/project-config.md` — [pending or not needed]
```

### 2. Update CLAUDE.md

If the learning implies a rule or guideline that should apply to future work:

- Add a concise entry to the appropriate section of `CLAUDE.md`
- Place it in a relevant section (architecture, coding, testing, etc.)
- Keep it brief — one or two lines maximum
- If `CLAUDE.md` doesn't exist yet, create it with a minimal structure

**Do NOT bloat CLAUDE.md.** Each entry should be actionable and specific. Prefer:
> "Always use parameterized queries for database access — see docs/learnings/2026-02-11-sql-injection.md"

Over:
> "We learned that SQL injection is a risk when building database queries, and we should always use parameterized queries to prevent this. This was discovered when building the user search feature where we initially used string concatenation..."

### 3. Optionally suggest project-config updates

If a learning implies a project-specific standard that should be codified:

- Suggest an update to `.claude/project-config.md`
- Explain why this should be a project standard
- Wait for engineer approval before making the change

## Phase 4: Avoid Duplicates

Before proposing any learning, check for duplicates:

1. **Check `docs/learnings/`** — Read existing learning documents. Does this learning already exist?
2. **Check `CLAUDE.md`** — Is this already captured as a rule or guideline?
3. **Check `.claude/project-config.md`** — Is this already a project standard?

If a learning overlaps with an existing one:
- If it adds new context or a better example → propose updating the existing learning
- If it's truly redundant → skip it silently

## Integration

- **FED BY:** `fulcrum:spec-driven-development` — specs provide the original intent for comparison
- **UPDATES:** `CLAUDE.md` — project rules and guidelines
- **UPDATES:** `.claude/project-config.md` — project-specific standards (with engineer approval)
- **WORKS WITH:** `fulcrum:finishing-a-development-branch` — natural point to suggest running `/compound`

## Verification Checklist

Before considering compound learning complete:
- [ ] Correct cycle was identified and confirmed with the engineer
- [ ] Existing learnings were checked for duplicates
- [ ] Each proposed learning includes category, description, context, and example
- [ ] Engineer approved each learning before it was applied
- [ ] Learning documents saved to `docs/learnings/`
- [ ] CLAUDE.md updated with concise, actionable entries (if applicable)
- [ ] No bloat was added — each entry is specific and brief
- [ ] Engineer was not nagged if no learnings were found
