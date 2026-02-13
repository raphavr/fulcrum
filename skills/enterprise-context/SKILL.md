---
name: enterprise-context
description: Use when starting a session, generating specs or plans, reviewing code, or when the user asks about company coding standards, architecture patterns, security requirements, or testing conventions
---

# Enterprise Context

## Overview

Enterprise context automatically injects company-wide configuration (coding standards, architecture patterns, security requirements, git workflow) into the session. It loads structured config files, applies phase-specific filtering, and merges with project-level overrides.

## When to Use

- **Automatically** at the start of any session
- **During spec generation** — to ensure specs reflect company standards
- **During plan generation** — to include testing and workflow standards
- **During code review** — to check all standards comprehensively
- **On demand** — when the engineer asks "what are our coding standards", "what's our architecture pattern", or similar

## Configuration Hierarchy

Configuration merges in this priority order (highest wins):

```
Level 3: .claude/CLAUDE.md              — Standard Claude Code project rules (highest priority)
Level 2: .claude/project-config.md      — Project-specific overrides
Level 1: config/company-standards/*.yaml — Company-wide defaults (lowest priority)
```

There is **no team-level configuration** — team structures change too frequently to be a reliable config boundary.

## Company Standards Location

Company-wide standards live in the plugin repo at:

```
config/company-standards/
├── architecture.yaml       # Architecture patterns (~500 tokens)
├── coding-standards.yaml   # Coding conventions (~800 tokens)
├── security.yaml           # Security requirements (~400 tokens)
├── testing.yaml            # Testing standards (~300 tokens)
└── git-workflow.yaml       # Git workflow rules (~200 tokens)
```

## Phase-Specific Loading

Only load the config sections relevant to the current workflow phase. This keeps context usage efficient.

| Phase | Config Sections Loaded |
|-------|----------------------|
| **Spec** | architecture + coding-standards + security |
| **Plan** | testing + git-workflow |
| **Implement** | coding-standards only |
| **Review** | all sections (comprehensive review) |
| **On demand** | all sections |

### How to Load

1. Read the relevant YAML files from `config/company-standards/` in the plugin directory.
2. Check if `.claude/project-config.md` exists in the current project repo.
3. If project config exists, parse it and identify any overrides.
4. Apply overrides: project-specific values replace company defaults for the same keys.
5. Present the merged configuration as context for the current phase.

## Project Configuration Overrides

Projects can override specific company settings by creating `.claude/project-config.md` in their repo:

```yaml
# Project-specific overrides
architecture:
  communication_pattern: "sync-http"  # Override: this service doesn't use events

testing:
  min_coverage: 90  # Higher than company default

git_workflow:
  branch_naming: "CHECKOUT-{brief-description}"  # Project-specific prefix
```

## Presenting Context

When injecting context, present it clearly:

**During spec phase:**
> Applying company standards: architecture (hexagonal pattern), coding standards (Airbnb TypeScript), security (parameterized queries required).

**During plan phase:**
> Applying company standards: testing (80% coverage, unit + integration required), git workflow (squash merge, 1 reviewer minimum).

**On demand:**
> Present all company standards organized by category, noting any project-specific overrides.

## Error Handling

Configuration issues must NEVER block the workflow:

| Situation | Behavior |
|-----------|----------|
| Company config file missing | Log warning, use project config only, continue |
| Project config malformed | Log error, use company config only, continue |
| Both unavailable | Continue without config injection |
| YAML parse error | Log the specific error, skip that file, continue |

When degraded, inform the engineer:
> Note: Could not load `security.yaml` from company standards. Proceeding with project config only.

## Tracking

Track which config sections were loaded for metrics purposes. When config is injected, note it so the metrics hooks can include this information:

```
Sections loaded: [architecture, coding-standards, security]
Project overrides applied: [architecture.communication_pattern]
```

## Integration

- **USED BY:** `fulcrum:spec-driven-development` during spec generation
- **USED BY:** `superpowers:writing-plans` during plan generation
- **USED BY:** `superpowers:requesting-code-review` during code review
- **STANDALONE:** Responds to direct questions about company standards

## Verification Checklist

Before considering context injection complete:
- [ ] Relevant config files were read (or absence was handled gracefully)
- [ ] Phase-specific filtering was applied (not all sections loaded unnecessarily)
- [ ] Project overrides were checked and applied if present
- [ ] Engineer was informed of what standards are active
- [ ] Any missing or malformed configs were logged but did not block workflow
