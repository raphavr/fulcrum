---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Enterprise context:** Invoke `fulcrum:enterprise-context` for the plan phase (testing + git-workflow standards).

**Context:** This should be run in a dedicated worktree (created by /spec or using-git-worktrees skill).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Pre-flight Check

Before writing any tasks, verify the required standards are documented and available. **Do not proceed if either is missing.**

### 1. Test patterns — from `CLAUDE.md`

Read the project's `CLAUDE.md`. It must document:
- The exact command to run tests
- How test files are named and where they live
- The test structure/pattern to follow

**If CLAUDE.md doesn't exist or doesn't document test patterns:**
> ⚠ Cannot write plan: `CLAUDE.md` is missing test patterns (test command, file location, test structure). Add them to `CLAUDE.md` before proceeding.

Stop. Do not continue.

### 2. Commit convention — from enterprise context

`fulcrum:enterprise-context` must have been loaded for the plan phase (includes `git-workflow.yaml`). It provides `commit_format`.

**If enterprise context was not loaded or `commit_format` is absent:**
> ⚠ Cannot write plan: git-workflow standards are not available. Ensure `fulcrum:enterprise-context` ran successfully for the plan phase.

Stop. Do not continue.

---

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## Task Structure

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/new-file`
- Modify: `exact/path/to/existing-file:123-145`
- Test: `exact/path/to/test-file` ← location per CLAUDE.md

**Step 1: Write the failing test**

In `exact/path/to/test-file`, add:

[Complete test code following the test structure documented in CLAUDE.md]

**Step 2: Run test to verify it fails**

Run: `[test command from CLAUDE.md, scoped to this file/test]`
Expected: FAIL — "[specific error that confirms the test is wired correctly, not a syntax error]"

**Step 3: Write minimal implementation**

In `exact/path/to/new-file`, add:

[Complete implementation following the coding standards in CLAUDE.md and enterprise-context.
Only what makes this test pass — no speculative code.]

**Step 4: Run test to verify it passes**

Run: `[same command as Step 2]`
Expected: PASS

**Step 5: Commit**

```bash
git add exact/path/to/test-file exact/path/to/new-file
git commit -m "[commit message using commit_format from git-workflow.yaml]"
```
```

## Remember
- Exact file paths always — no generic placeholders
- Complete code in every step — not "add validation here" but the actual code
- Test command and structure come from `CLAUDE.md` — never infer from existing code
- Coding standards come from `CLAUDE.md` and enterprise-context — never infer from existing code
- Commit format comes from enterprise git-workflow — never invent one
- DRY, YAGNI, TDD, frequent commits

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/plans/<filename>.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use superpowers:subagent-driven-development
- Stay in this session
- Fresh subagent per task + code review

**If Parallel Session chosen:**
- Guide them to open new session in worktree
- **REQUIRED SUB-SKILL:** New session uses superpowers:executing-plans
