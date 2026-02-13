# Architecture Decision Record: Software Delivery Fulcrum

**Status:** In Progress  
**Date:** 2026-02-11  
**Context:** Building an enterprise software delivery fulcrum to help engineering teams leverage AI more effectively while respecting existing workflows and proving value through metrics.

---

## Problem Statement

Most software engineers are not yet heavily using agentic AI for development. The goal is to create a structured workflow system that:
- Reduces cognitive load in software development
- Bridges task context to pull requests
- Proves AI value through comprehensive metrics
- Respects existing engineering workflows (doesn't force wholesale changes)
- Accommodates senior engineers who prefer traditional approaches
- Enables team learning and continuous improvement

---

## Decision 1: Use Superpowers as Foundation

### Context
We evaluated several foundation repositories for building the fulcrum:
- obra/superpowers
- jtmuller5/Everything-Claude-Code
- NeoLab-io/Context-Engineering-Kit
- getgrit/compound-engineering

### Decision
**Fork [obra/superpowers](https://github.com/obra/superpowers) v4.1.1 (MIT license) as the base.**

### Rationale

**Strengths of Superpowers:**
- **Composable skills framework** where skills trigger automatically based on context
- **Incremental adoption** - provides structure but doesn't force it
- **Built-in quality gates** - mandatory workflow phases with verification points
- **Active community** - 10+ external contributors, regular updates
- **Clean MIT license** - suitable for enterprise use without restrictions
- **Natural extension points** - plugin architecture designed for customization
- **Git worktree isolation** - prevents main branch interference during development
- **Subagent-driven development** - breaks work into manageable batches
- **Two-stage code review** - separates spec compliance from code quality checks

**Why Not Others:**
- **Everything Claude Code**: More feature-complete but also more opinionated; harder to extend without breaking existing patterns; smaller community
- **Context Engineering Kit**: Excellent SDD patterns but focused on single-workflow approach; we need the flexibility Superpowers provides
- **Compound Engineering**: Perfect for learning patterns but lacks the structured workflow orchestration we need

**Approach:**
We will **preserve all existing Superpowers functionality** and add enterprise extensions on top. This ensures:
- Upstream changes remain mergeable
- Engineers can use base Superpowers features if they prefer
- We benefit from community improvements
- Clear separation between base functionality and our additions

---

## Decision 2: Add Compound Learning Step

### Context
Software development generates valuable knowledge that's typically lost: what worked, what didn't, patterns discovered, gotchas encountered. This knowledge could improve future development cycles if captured systematically.

### Decision
**Add a compound learning skill that captures post-cycle knowledge and feeds it back into project configuration.**

### Rationale

**Borrowed from Compound Engineering:**
- The compound learning pattern has proven effective in practice
- Post-cycle reflection when context is fresh yields better learnings
- Feeding learnings back into `CLAUDE.md` and project docs creates a virtuous cycle

**Adapted for Superpowers:**
- Integrated as an optional skill, not mandatory workflow step
- Invoked via `/compound` command (engineer chooses when to run it)
- Learnings stored in `docs/learnings/` alongside specs
- Clear connection between specs → implementation → learnings

**Value Proposition:**
- Project-specific patterns accumulate over time
- New team members get immediate context about project conventions
- Common issues are documented with solutions
- Reduces repeated mistakes

**Key Design Principle:**
Learnings must be **optional and non-nagging**. If an engineer doesn't want to capture learnings for a cycle, that's fine. The system should never force or pressure learning capture.

---

## Decision 3: Metrics Collection via Hooks (Not Skills)

### Context
We need comprehensive metrics to prove AI value and identify improvement areas. Two approaches were considered:
1. **Skills emit metrics** - each skill writes metrics events
2. **Hooks collect metrics** - session boundaries (start/stop) gather data from artifacts

### Decision
**Use hooks (SessionStart, SessionStop) for deterministic metrics collection, with minimal state tracking in skills.**

### Rationale

**Why Hooks:**
- **Guaranteed execution** - SessionStop always fires when Claude Code exits
- **Deterministic** - runs exactly once per session, predictable timing
- **Centralized logic** - all metrics collection in one place
- **Failure resilient** - if a skill forgets to emit, hooks still capture session-level data
- **Non-invasive** - minimal changes to skills (just state file writes)

**Why Not Skill-Based Emission:**
- **Agent unreliability** - LLMs occasionally skip instructions; metrics would be incomplete
- **Skill bloat** - every skill would need metrics logic, increasing complexity
- **Token overhead** - metrics instructions in every skill context
- **Inconsistency** - different skills might emit different event shapes

**Hybrid Pattern (v1 Implementation):**
- **Hooks handle emission** - guaranteed to fire, produce to Kafka topic
- **Skills write state transitions** - minimal instruction: "append to .claude/workflow-state.jsonl"
- **Hooks read artifacts** - parse state file, check git activity, find created specs
- **Result:** Reliable metrics without requiring agent perfection

**Future Enhancement (v2+):**
When richer metrics are needed, skills can write additional detail to state file (review findings, subagent counts), and hooks emit the enriched data. This preserves the deterministic emission guarantee while allowing optional enrichment.

---

## Decision 4: Enterprise Context - Structured Git-Based Config

### Context
Engineers need access to company-wide standards (coding conventions, architecture patterns, security requirements, git workflow) without manually managing configuration files. The configuration must be:
- **Centralized** - one source of truth, managed by platform team
- **Automatic** - no per-project setup required
- **Token-efficient** - minimize context window consumption
- **Low friction** - no additional setup beyond plugin installation

### Decision
**Use structured git-based config with phase-specific smart loading (Option D).**

Company configuration is organized into focused YAML files in the plugin repo:
```
config/company-standards/
├── architecture.yaml       # ~500 tokens
├── coding-standards.yaml   # ~800 tokens
├── security.yaml           # ~400 tokens
├── testing.yaml            # ~300 tokens
└── git-workflow.yaml       # ~200 tokens
```

The `enterprise-context` skill intelligently loads **only relevant sections** per workflow phase:
- **Spec phase** → architecture + coding-standards + security
- **Plan phase** → testing + git-workflow
- **Implement phase** → coding-standards only
- **Review phase** → all sections (comprehensive review)

### Rationale

**Token Efficiency:**
- Full config might be 2-3KB, but we only load 1000-1500 tokens per phase
- Better than loading entire config every time
- Achieves similar optimization to MCP without the complexity

**Zero Setup Friction:**
- Engineers just run `/plugin install fulcrum`
- Config comes with the plugin automatically
- No MCP server to install/configure
- Works offline by design

**Simple Distribution:**
- Platform team updates config files in plugin repo
- Engineers run `/plugin update fulcrum` to get new standards
- Clear versioning (config version = plugin version)
- Standard git workflow for config changes

**Maintainable:**
- Each config file is small, focused, and reviewable
- Team members can contribute improvements via PR
- No infrastructure to maintain
- Easy to see what changed between versions

**Graceful Degradation:**
- If config file missing: skill logs warning, continues with project config
- If project config also missing: workflow continues unblocked
- No network dependencies to fail

### Why Not Other Options

**MCP (Option C):** Overkill for static company-wide configuration. MCP excels at dynamic, user-specific data (like Jira integration in v2), but company standards change monthly at most. Setup friction (npm install, configuration) isn't justified.

**Single-file git config (Option A):** Loading entire config every time wastes tokens. As standards grow, this becomes expensive.

**HTTP fetch (Option B):** Adds infrastructure dependency and network failure mode without significant benefits over git-based distribution.

**Project-only (Option E):** Loses standardization across projects. Company policies become harder to enforce.

### Implementation Notes

Plugin version is tracked in metrics to correlate config changes with workflow outcomes. This enables analysis like "did the v1.5 coding standards update improve code review pass rates?"

---

## Decision 5: Orchestration Approach

### Context
Two ways to orchestrate the workflow:
1. **Claude Code manages workflow** - commands, skills, and hooks drive state transitions
2. **Thin CLI wrapper** - external script controls state, invokes Claude Code for each phase

### Decision
**Use Claude Code's built-in orchestration (commands + skills + hooks).**

### Rationale

**Why Agent-Driven:**
- **Natural for engineers** - works like normal Claude Code, just with structure
- **Flexible** - engineers can deviate from workflow when needed
- **Leverages Superpowers** - already has workflow patterns built-in
- **No additional tooling** - no wrapper CLI to maintain
- **Better debugging** - state is visible in conversation, not hidden in wrapper logs

**Why Not Wrapper CLI:**
- Adds complexity - another tool to install/maintain
- Hides context - conversation doesn't show full workflow state
- Harder to deviate - engineer loses control when wrapper is in charge
- Duplication - wrapper would replicate logic that skills already have

**Trade-off Accepted:**
Agent-driven orchestration is less deterministic than a CLI wrapper. The agent might skip steps or deviate from the workflow. We accept this because:
- The value of flexibility outweighs the cost of occasional deviations
- Hooks provide deterministic boundaries (session start/end always fire)
- Engineers should have agency to override the workflow when appropriate

---

## Decision 6: Source Control - Bitbucket Not GitHub

### Context
The team uses **Bitbucket** (not GitHub) for source control and CI/CD.

### Decision
**Remove all GitHub-specific assumptions and keep git operations generic.**

### Implications
- No GitHub Actions references
- No GitHub PR API automation (v1)
- Git worktrees, branches, commits work the same regardless of remote
- Future PR automation must use Bitbucket APIs
- Bitbucket Pipelines (not GitHub Actions) for CI/CD integration

---

## Decision 7: Phase Out Jira Integration (v1)

### Context
Original spec included Jira integration to pull ticket context into workflows. However, most tasks don't have good descriptions in Jira, limiting the value.

### Decision (Revised)
**Remove Jira integration from v1. Focus on core workflow and metrics first.**

### Rationale
- Task descriptions in Jira are often incomplete or outdated
- Adds complexity (MCP server setup, API configuration)
- Workflow works fine without Jira - engineers can provide context directly
- Can add back in v2 once core workflow proves value

**What This Means:**
- Remove `skills/jira-integration/`
- Remove Jira MCP server references
- Remove Jira-related config from enterprise context
- Ticket ID can still be mentioned manually - just not auto-fetched

---

## Decision 8: Single Entry Point — /spec Handles All Feature Work

### Context
An early design had two separate entry points: `/spec` for well-defined tasks and `/brainstorm` for exploratory ideas. Both fed into the same plan → implement pipeline, creating overlapping flows and a decision burden ("which one do I use?").

The two flows shared more than they differed. Both did codebase analysis; both produced a plan; both executed the same pipeline. The only real difference was whether a dialogue phase ran before analysis. The brainstorm flow also produced a design doc rather than a spec, creating a traceability gap — exploratory work had no spec artifact.

### Decision
**A single `/spec` command is the entry point for all feature work. The `spec-driven-development` skill adapts based on input clarity.**

### Rationale

**Eliminates the entry-point decision:**
- Engineers use `/spec` regardless of how formed the idea is
- The skill detects vague vs. well-defined input and adapts

**Always produces a spec artifact:**
- All feature work has a spec in `docs/specs/`
- Spec → plan → implementation → PR chain is complete and traceable

**Adaptive Phase 0:**
- Vague input → dialogue phase (one question at a time, 2-3 approaches, YAGNI-focused) → transitions to codebase analysis
- Well-defined input → skip Phase 0, go straight to analysis
- The skill announces the transition so the engineer sees where they are

**Clean command surface:**
- `/spec` — entry point for all feature work
- `/write-plan` — mid-pipeline entry point (skip spec when requirements are already locked)
- `/execute-plan` — execute an existing plan in a new session
- `/compound` — post-cycle knowledge capture

---

## Decision 9: Kafka for Metrics Transport + Vendored kafkajs

### Context
Hooks need to emit events to a backend without relying on anything beyond what Claude Code CLI guarantees. Two transport options were considered:
1. **HTTP POST** — simple, but requires `FULCRUM_METRICS_URL` and a receiving endpoint
2. **Kafka producer** — decoupled, replayable, fits enterprise data pipelines

For the Kafka client dependency, runtime installation was also considered:
1. **npm install at runtime** — unreliable: `npm` is not guaranteed to be in PATH in non-interactive shells (nvm, Volta, restricted environments)
2. **Vendor the library** — copy source into `hooks/vendor/kafkajs/`; works wherever `node` runs

### Decision
**Produce metrics events to a Kafka topic via a vendored kafkajs.**

### Rationale

**Why Kafka over HTTP:**
- **Decoupled** — hooks don't depend on a specific backend URL or availability
- **Replayable** — events can be replayed if consumers are down
- **Enterprise-native** — fits existing data pipeline infrastructure
- **Single topic** — all event types flow to one topic; consumers filter by `event_type`

**Why Vendor over Runtime Install:**
- **Node.js is the only guaranteed runtime** — Claude Code CLI requires it; nothing else is certain
- **npm not in PATH** — version managers (nvm, Volta) only inject PATH in interactive shells; hooks run as non-interactive child processes
- **kafkajs has zero production dependencies** — vendoring is safe and self-contained (~1.8MB)
- **No network required** — works in air-gapped and CI environments
- **Deterministic** — no version drift, no install failures

### Event Schema
All events share fixed fields + a `metadata` object for event-specific data:
```json
{ "event_type": "...", "timestamp": "...", "session_id": "...",
  "project": "...", "plugin_version": "...", "metadata": { } }
```
Message key = `session_id` for partition locality.

### Configuration
| Env Var | Purpose | Required |
|---|---|---|
| `FULCRUM_KAFKA_BROKERS` | Comma-separated broker list | Yes |
| `FULCRUM_KAFKA_TOPIC` | Single topic for all events | Yes |
| `FULCRUM_KAFKA_CLIENT_ID` | Producer ID (default: `fulcrum-plugin`) | No |
| `FULCRUM_KAFKA_SSL` | Enable TLS (`true`/`false`) | No |
| `FULCRUM_KAFKA_SASL_USERNAME` | SASL plain username | No |
| `FULCRUM_KAFKA_SASL_PASSWORD` | SASL plain password | No |

When required vars are absent the producer skips silently — no crash, just a console warning.

### Trade-offs Accepted
- **~1.8MB committed** — kafkajs source in `hooks/vendor/`; manual bump required on upgrades
- **Kafka required** — engineers must configure broker access; without env vars metrics are silently skipped

---

## Non-Decisions (Deferred to Later)

### Not Building in v1:
- **Automatic PR creation** - engineer creates PR manually
- **Real-time Jira updates** - no write-back to Jira
- **Metrics dashboard** - hooks emit events, separate system collects/displays
- **Team-level configuration** - company and project levels only
- **Multi-ticket workflows** - one ticket per cycle
- **Offline operation UX** - basic error handling only

### Future Considerations:
- **Superpowers upstream sync process** - how often to merge changes?
- **Cross-project learning sharing** - promoting learnings to company config?
- **Metrics privacy** - anonymized engineer IDs by default?
- **MCP server hosting model** - centralized HTTP vs local stdio?
- **Plugin size / token budget** - monitoring and optimization strategy?

---

## Success Criteria

The fulcrum succeeds if:

1. **Adoption** - Engineers choose to use it (not mandated)
2. **Workflow efficiency** - Measurable time savings or quality improvements
3. **Metrics prove value** - Clear ROI from data collected
4. **Team learning** - Knowledge accumulates and improves outcomes
5. **Minimal friction** - Setup is quick, usage respects existing workflows
6. **Scalability** - Works for teams of 5-50+ engineers without customization per team

---

## Open Action Items

- [ ] **Define config update cadence** - How often should company standards change? Recommend quarterly major updates, monthly minor updates
- [ ] **Establish upstream sync process** - Monthly Superpowers merges? Quarterly?
- [ ] **Define metrics privacy policy** - Anonymized by default or opt-in?
- [ ] **Create config contribution guidelines** - How do teams propose changes to company standards?
