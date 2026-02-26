# Fulcrum — Enterprise Software Delivery Plugin

This is a unified Claude Code plugin that combines Superpowers' core skills library with enterprise extensions for spec-driven development, company standards, metrics collection, and compound learning.

## Architecture

- **Skills** live in `skills/<name>/SKILL.md` — frontmatter description describes triggering conditions only ("Use when..."), never the workflow
- **Commands** live in `commands/<name>.md` — thin wrappers that delegate to skills
- **Hooks** live in `hooks/` — `session-start.sh` bootstraps skills context; `metrics-session-*.js` collect workflow metrics
- **Company config** lives in `config/company-standards/*.yaml` — structured YAML, phase-specific loading
- **Plugin metadata** lives in `.claude-plugin/`

## All Available Skills

### Core Workflow
- `writing-plans` — Detailed implementation planning (mid-pipeline entry: use when requirements are clear and no spec is needed)
- `subagent-driven-development` — Execute plans with independent subagents
- `executing-plans` — Multi-session plan execution
- `dispatching-parallel-agents` — Concurrent subagent workflows

### Quality & Review
- `test-driven-development` — Write test first, then implement
- `requesting-code-review` — Pre-merge code review
- `receiving-code-review` — Code review feedback implementation
- `verification-before-completion` — Pre-completion verification
- `systematic-debugging` — 4-phase root cause analysis

### Workflow Management
- `using-git-worktrees` — Isolated workspace management
- `finishing-a-development-branch` — Branch completion and cleanup
- `writing-skills` — Skill creation and testing

### Enterprise Fulcrum (new)
- `spec-driven-development` — `/spec` entry point: adaptive dialogue (if vague) → codebase analysis → structured spec → plan → execute
- `enterprise-context` — Auto-inject company standards (phase-specific: spec/plan/implement/review)
- `compound-learning` — `/compound` entry point: post-cycle knowledge capture

## Key Conventions

- Skill descriptions MUST start with "Use when..." — triggering conditions only, never workflow summary
- Commands are thin wrappers — one line delegating to a skill
- Cross-reference all skills as `fulcrum:skill-name`
- Hooks use `${CLAUDE_PLUGIN_ROOT}` for portable path resolution

## Metrics State Files

Skills write stage transitions to `.claude/workflow-state.jsonl`:
```
{"stage":"spec","action":"entered","timestamp":"<ISO8601>"}
{"stage":"spec","action":"completed","timestamp":"<ISO8601>"}
```

Valid stages and which skill writes them:
| Stage     | Written by                                                              |
|-----------|-------------------------------------------------------------------------|
| spec      | spec-driven-development (reinitializes file at Phase 1 start)          |
| plan      | writing-plans                                                           |
| implement | executing-plans OR subagent-driven-development                          |
| review    | requesting-code-review OR subagent-driven-development (final reviewer)  |
| finish    | finishing-a-development-branch                                          |

Note: `spec-driven-development` overwrites the file at Phase 1 start (new feature cycle). All other skills append.

## Company Standards

Edit `config/company-standards/*.yaml` for your organization. Projects override defaults via `.claude/project-config.md`.
