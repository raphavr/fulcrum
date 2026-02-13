# Software Delivery Fulcrum — Implementation Specification v1

## Project Overview

Build an enterprise software delivery fulcrum that extends [obra/superpowers](https://github.com/obra/superpowers) (MIT licensed) to create a structured workflow system with comprehensive metrics collection. The target audience is software engineering teams where **most engineers are not yet heavily using agentic AI** for development.

The fulcrum is a **fork of Superpowers** with additional skills, commands, and hooks designed for enterprise deployment. It does **not** replace Claude Code CLI — it extends it through the plugin/skills system.

---

## What We're Building (v1)

1. **Spec-Driven Development Skill + `/spec` Command** — Adaptive entry point for all feature work (exploratory or well-defined); always produces a spec artifact
2. **Enterprise Context Injection** — Company-wide standards automatically available (approach TBD - see ADR)
3. **Metrics Instrumentation Hooks** — Deterministic event collection at session boundaries
4. **Compound Learning Skill + `/compound` Command** — Post-cycle knowledge capture

### What We're NOT Building (v1)

- Jira integration (deferred to v2)
- Custom CLI wrapper (we use Claude Code CLI directly)
- Metrics collection backend / dashboard (hooks emit events, backend is separate)
- Automatic PR creation (engineer creates PR manually)

---

## Repository Structure

```
fulcrum/                              # Root of the forked repo
├── .claude-plugin/
│   ├── plugin.json                       # Plugin metadata (extends Superpowers)
│   └── marketplace.json                  # Marketplace catalog entry
│
├── skills/                               # All skills (Superpowers originals + new)
│   ├── writing-plans/                    # [UPSTREAM] Original Superpowers skill
│   │   └── SKILL.md
│   ├── subagent-driven-development/      # [UPSTREAM] Original Superpowers skill
│   │   └── SKILL.md
│   ├── requesting-code-review/           # [UPSTREAM] Original Superpowers skill
│   │   └── SKILL.md
│   ├── finishing-a-development-branch/   # [UPSTREAM] Original Superpowers skill
│   │   └── SKILL.md
│   ├── test-driven-development/          # [UPSTREAM] Original Superpowers skill
│   │   └── SKILL.md
│   ├── systematic-debugging/             # [UPSTREAM] Original Superpowers skill
│   │   └── SKILL.md
│   ├── using-git-worktrees/              # [UPSTREAM] Original Superpowers skill
│   │   └── SKILL.md
│   ├── verification-before-completion/   # [UPSTREAM] Original Superpowers skill
│   │   └── SKILL.md
│   ├── writing-skills/                   # [UPSTREAM] Original Superpowers skill
│   │   └── SKILL.md
│   │
│   ├── spec-driven-development/          # [NEW] Adaptive entry point (/spec)
│   │   └── SKILL.md
│   ├── enterprise-context/               # [NEW] Company config injection
│   │   └── SKILL.md
│   └── compound-learning/                # [NEW] Post-cycle knowledge capture
│       └── SKILL.md
│
├── commands/                             # Slash commands
│   ├── spec.md                           # [NEW] /spec — adaptive entry point (all feature work)
│   ├── write-plan.md                     # [UPSTREAM] /write-plan — mid-pipeline entry
│   ├── execute-plan.md                   # [UPSTREAM] /execute-plan
│   └── compound.md                       # [NEW] /compound — trigger learning capture
│
├── hooks/
│   ├── hooks.json                        # Hook definitions (SessionStart + Stop)
│   ├── metrics-session-start.js          # Session start metrics collection
│   ├── metrics-session-end.js            # Session end metrics collection + emission
│   ├── kafka-producer.js                 # Shared Kafka producer (env-var configured)
│   ├── kafka-producer.test.js            # Unit tests (node:test, zero extra deps)
│   ├── package.json                      # Test script only — no install-time deps
│   └── vendor/
│       └── kafkajs/                      # Vendored kafkajs (zero prod deps, ~1.8MB)
│
├── config/
│   └── company-standards/                # Company-wide configuration (structured)
│       ├── architecture.yaml             # Architecture patterns (~500 tokens)
│       ├── coding-standards.yaml         # Coding conventions (~800 tokens)
│       ├── security.yaml                 # Security requirements (~400 tokens)
│       ├── testing.yaml                  # Testing standards (~300 tokens)
│       └── git-workflow.yaml             # Git workflow rules (~200 tokens)
│
├── docs/
│   ├── adoption-guide.md                 # How to roll out to engineering teams
│   ├── metrics-schema.md                 # Event schema documentation
│   └── architecture.md                   # Technical architecture overview
│
├── CLAUDE.md                             # Bootstrap instructions for the fulcrum itself
└── README.md                             # Installation and usage guide
```

### Naming Conventions

- Skill directories: `kebab-case/` with `SKILL.md` inside
- Command files: `kebab-case.md` in `commands/`
- All new skills and commands must include a frontmatter block per Superpowers conventions
- Skill descriptions must follow Superpowers' rule: describe **triggering conditions** only, never summarize the workflow

---

## Detailed Skill Specifications

### 1. Spec-Driven Development Skill (`skills/spec-driven-development/SKILL.md`)

#### Purpose
Provide the primary entry point to the Superpowers workflow — adaptive for both exploratory and well-defined inputs. Transforms any feature idea into a structured specification through codebase analysis and optional dialogue, then feeds that spec into Superpowers' existing plan → implement pipeline.

#### Triggering Conditions
- User invokes `/spec` command
- User says "create a spec for", "write a spec", "I need a specification", "let's build X", "I want to add a feature"

#### Behavior

The flow has four phases:

**Phase 0: Clarity Check (adaptive)**

If the input is vague or exploratory:
1. Ask questions one at a time to refine the idea (prefer multiple-choice)
2. Propose 2-3 approaches with trade-offs; lead with recommendation
3. Apply YAGNI ruthlessly — remove unnecessary scope
4. Transition to Phase 1 when goal is clear

If the input is already well-defined: skip directly to Phase 1.

**Phase 1: Task Specification**

1. Accept input: natural language prompt from engineer describing what needs to be built.

2. Analyze the existing codebase to understand:
   - Which files and modules are likely affected (codebase impact analysis)
   - Existing patterns in the affected areas (naming conventions, architecture patterns, test patterns)
   - Related recent changes (git log analysis of affected files)

3. Generate a structured task specification document containing:
   - **Goal**: One-sentence summary of what needs to happen
   - **Context**: Relevant codebase state, affected files, existing patterns
   - **Requirements**: Explicit list derived from the input
   - **Constraints**: Technical constraints discovered from codebase analysis
   - **Impact Analysis**: Files to modify, files to create, files to delete
   - **Out of Scope**: Explicitly list what this task does NOT include
   - **Risks**: Potential issues identified from the analysis

4. Present the spec to the engineer in digestible sections (following Superpowers' pattern of chunked presentation) for review and approval.

5. Allow iterative refinement: engineer can modify sections, ask for alternatives, or add constraints.

**Phase 2: Plan Generation (bridges to Superpowers' `writing-plans` skill)**

Once the spec is approved:

1. Transform the spec into a Superpowers-compatible implementation plan.
2. Break the work into tasks following Superpowers' conventions (2-5 minutes each, TDD-oriented, clear enough for a subagent to execute).
3. Each task references back to the spec requirement it fulfills.
4. Present the plan for approval (standard Superpowers plan approval flow).

**Phase 3: Execution (delegates to Superpowers' existing pipeline)**

Once the plan is approved, execution follows the standard Superpowers pipeline:
- Git worktree creation (if not already in one)
- Subagent-driven development
- Two-stage code review between tasks
- Verification before completion

#### Spec Document Format

The spec document is saved to `docs/specs/` in the project directory:

```
docs/specs/
└── 2026-02-11-add-user-notifications.md    # Named by date + description
```

Spec document structure:

```markdown
# Task Specification: [Title]

**Created:** 2026-02-11
**Status:** Draft | Approved | Implemented

## Goal
[One sentence]

## Context
[Codebase state, relevant architecture, recent changes in affected areas]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] ...

## Constraints
- [Technical constraints from codebase analysis]

## Impact Analysis
### Files to Modify
- `path/to/file.ts` — [what changes and why]

### Files to Create
- `path/to/new-file.ts` — [purpose]

### Files to Delete
- (none expected)

## Out of Scope
- [Explicit exclusions]

## Risks
- [Identified risks and mitigations]
```

#### Key Design Principle: Spec as a First-Class Artifact

The spec document is NOT disposable. It:
- Lives in the repo alongside the code (`docs/specs/`)
- Gets committed with the implementation
- Serves as documentation of intent for future maintainers
- Is the foundation for the compound learning step (what matched the spec vs. what diverged)
- Provides traceability from spec → plan → implementation → PR

---

### 2. Enterprise Context Skill (`skills/enterprise-context/SKILL.md`)

#### Purpose
Automatically inject company-wide configuration (coding standards, architecture patterns, security requirements, git workflow) into the session without requiring manual engineer intervention.

#### Triggering Conditions
- Automatically at session start
- When generating specs or plans (to ensure standards are applied)
- When the engineer explicitly asks "what are our coding standards" or similar

#### Behavior

1. **Load company configuration** from structured config files in the plugin repo:
   ```
   config/company-standards/
   ├── architecture.yaml       # ~500 tokens
   ├── coding-standards.yaml   # ~800 tokens
   ├── security.yaml           # ~400 tokens
   ├── testing.yaml            # ~300 tokens
   └── git-workflow.yaml       # ~200 tokens
   ```

2. **Smart phase-specific loading** - only load relevant sections:
   - **Spec phase** → architecture + coding-standards + security
   - **Plan phase** → testing + git-workflow
   - **Implement phase** → coding-standards only
   - **Review phase** → all sections (comprehensive review)

3. **Load project configuration** from `.claude/project-config.md` if present in the repo

4. **Merge configurations** with project overrides taking precedence over company defaults

5. **Track what was injected** for metrics (which config sections were used)

#### Configuration Hierarchy

```
Level 1: Company-wide standards    — config/company-standards/*.yaml (in plugin repo)
Level 2: .claude/project-config.md — Project-specific overrides (in project repo)
Level 3: .claude/CLAUDE.md         — Standard Claude Code project rules
```

There is **no team-level configuration** — team structures change too frequently to be a reliable config boundary.

#### Company Configuration Schema (Example)

**`config/company-standards/coding-standards.yaml`:**
```yaml
language_defaults:
  typescript:
    style_guide: "airbnb"
    max_line_length: 100
    prefer_const: true
  python:
    style_guide: "PEP8"
    max_line_length: 88

naming_conventions:
  files: "kebab-case"
  classes: "PascalCase"
  functions: "camelCase"
  constants: "UPPER_SNAKE_CASE"

max_file_length: 300
documentation_requirements: "All public functions must have JSDoc/docstring"
```

**`config/company-standards/architecture.yaml`:**
```yaml
backend_pattern: "hexagonal"
data_access_pattern: "repository"
communication_pattern: "event-driven"
api_versioning: true
```

**`config/company-standards/testing.yaml`:**
```yaml
min_coverage: 80
required_test_types: ["unit", "integration"]
e2e_required_for: ["critical_user_flows"]
test_file_location: "alongside source files"
```

**`config/company-standards/security.yaml`:**
```yaml
no_hardcoded_secrets: true
input_validation: "required"
parameterized_queries: "required"
auth_required: "all_non_public_endpoints"
```

**`config/company-standards/git-workflow.yaml`:**
```yaml
branch_naming: "{brief-description}"
commit_format: "{description}"
merge_strategy: "squash"
min_reviewers: 1
```

#### Project Configuration Override Example

Project can override specific settings in `.claude/project-config.md`:

```yaml
# Project-specific overrides for checkout-service
architecture:
  communication_pattern: "sync-http"  # Override: this service doesn't use events

testing:
  min_coverage: 90  # Higher than company default
  
git_workflow:
  branch_naming: "CHECKOUT-{brief-description}"  # Project-specific prefix
```

#### Distribution Strategy

**To update company standards:**
1. Platform team modifies files in `config/company-standards/` in the plugin repo
2. Changes committed and pushed via PR
3. New plugin version published
4. Engineers run `/plugin update fulcrum` to get new standards
5. Next session automatically picks up the new config

**Plugin version is tracked in metrics** to correlate config changes with workflow outcomes.

#### Error Handling

- If company config file is missing: Log warning, use project config only, workflow continues
- If project config is malformed: Log error, use company config only, workflow continues
- If both are unavailable: Workflow continues without config injection
- **Never block workflow due to config issues**

---

### 3. Compound Learning Skill (`skills/compound-learning/SKILL.md`)

#### Purpose
Capture knowledge from completed development cycles (what worked, what didn't, patterns discovered, gotchas encountered) and feed it back into project configuration to improve future cycles.

#### Triggering Conditions
- User invokes `/compound` command
- User says "capture learnings", "what did we learn", or similar
- Optionally: automatically suggested after finishing a branch (if engineer opts in)

#### Behavior

**Phase 1: Gather Cycle Data**

1. Identify the most recently completed cycle:
   - Check git log for recent commits
   - Find associated spec in `docs/specs/` (if it exists)
   - Find plan document (if /spec or /write-plan was used)
   - Identify files changed

2. Extract cycle context:
   - What was the goal? (from spec or commits)
   - What was the estimated complexity?
   - What was actually implemented?
   - Were there surprises or deviations from the plan?

**Phase 2: Identify Learnings**

Analyze the cycle for notable learnings in these categories:

- **Patterns**: Recurring code patterns or architectural decisions that worked well
- **Gotchas**: Problems encountered and how they were resolved
- **Tools**: Libraries, frameworks, or tools that were particularly useful or problematic
- **Process**: Aspects of the development workflow that helped or hindered
- **Project-specific**: Conventions or constraints specific to this project
- **False starts**: Approaches tried and abandoned (and why)

Present proposed learnings to the engineer. Each learning should include:
- Category (pattern/gotcha/tool/process/project-specific)
- Description (what was learned)
- Context (when does this apply)
- Example (concrete instance from the cycle)

**Phase 3: Apply Learnings**

For each approved learning:

1. **Update project docs:**
   - Append to `docs/learnings/YYYY-MM-DD-topic.md`
   - Format: Date, category, description, context, example

2. **Update CLAUDE.md:**
   - Add relevant learnings as rules or guidelines
   - Place in appropriate section (architecture/coding/testing)
   - Keep concise — don't bloat the file

3. **Optionally suggest `.claude/project-config.md` updates:**
   - If learning implies a project-specific standard
   - Engineer reviews before applying

**Phase 4: Avoid Duplicates**

Before proposing a learning:
- Check existing learnings in `docs/learnings/`
- Check existing rules in `CLAUDE.md`
- Only propose if it adds new information

#### Learning Document Format

```markdown
# Learning: [Topic]

**Date:** 2026-02-11
**Category:** Pattern | Gotcha | Tool | Process | Project-specific
**Cycle:** [Related spec or feature]

## Description
[What was learned]

## Context
[When does this apply? When is it not relevant?]

## Example
[Concrete instance from the cycle that demonstrates this learning]

## Applied To
- [x] `CLAUDE.md` — Added rule in Architecture section
- [x] `docs/learnings/` — This document
- [ ] `.claude/project-config.md` — (no config change needed)
```

#### Key Design Principles

- **Optional**: Engineer chooses when to run `/compound`, it's never forced
- **Non-nagging**: If no notable learnings in a cycle, say so and move on
- **Engineer approval**: Every learning must be approved before applying
- **Incremental**: One or two learnings per cycle is fine, don't force quantity
- **Avoid bloat**: Learnings should condense over time, not accumulate forever

---

## Hooks Implementation

### Overview

Hooks provide deterministic metrics collection at session boundaries. The SessionStart hook initializes state, and SessionStop hook reads artifacts and emits events.

### Hook Definitions (`hooks/hooks.json`)

```json
{
  "hooks": [
    {
      "event": "SessionStart",
      "script": "hooks/metrics-session-start.js"
    },
    {
      "event": "SessionStop",
      "script": "hooks/metrics-session-end.js"
    }
  ]
}
```

### SessionStart Hook (`hooks/metrics-session-start.js`)

**Purpose:** Initialize session tracking, generate session ID, detect project name.

**Implementation:**

```javascript
#!/usr/bin/env node
const fs = require('fs');
const crypto = require('crypto');
const { execSync } = require('child_process');

const sessionId = crypto.randomUUID();
const startTime = new Date().toISOString();

// Detect project name from git remote
let project = 'unknown';
try {
  const remoteUrl = execSync('git remote get-url origin', { encoding: 'utf8' }).trim();
  // Extract repo name from URL patterns:
  // git@bitbucket.org:company/checkout-service.git → checkout-service
  // https://bitbucket.org/company/checkout-service.git → checkout-service
  const match = remoteUrl.match(/\/([^\/]+?)(?:\.git)?$/);
  if (match) project = match[1];
} catch (e) { /* not a git repo or no remote */ }

// Get plugin version from plugin.json
let pluginVersion = 'unknown';
try {
  const pluginMeta = JSON.parse(fs.readFileSync('.claude-plugin/plugin.json', 'utf8'));
  pluginVersion = pluginMeta.version || 'unknown';
} catch (e) { /* plugin.json not found or malformed */ }

// Initialize state file
const stateDir = '.claude';
if (!fs.existsSync(stateDir)) fs.mkdirSync(stateDir, { recursive: true });
fs.writeFileSync(`${stateDir}/workflow-session.json`, JSON.stringify({
  session_id: sessionId,
  start_time: startTime,
  project,
  plugin_version: pluginVersion
}));

// Initialize empty state file for stage transitions
fs.writeFileSync(`${stateDir}/workflow-state.jsonl`, '');

const { sendEvent } = require('./kafka-producer');
sendEvent({ eventType: 'workflow.session.started', sessionId, project, pluginVersion }, {})
  .then(() => console.log(`[metrics] Session ${sessionId} started for project ${project} (plugin v${pluginVersion})`))
  .catch(err => console.error('[metrics] Unexpected error:', err.message));
```

### SessionStop Hook (`hooks/metrics-session-end.js`)

**Purpose:** Read artifacts (state file, git history, specs) and emit workflow.session.completed event.

**Implementation:**

```javascript
#!/usr/bin/env node
const fs = require('fs');
const { execSync } = require('child_process');

// Read session info
let session = {};
try {
  session = JSON.parse(fs.readFileSync('.claude/workflow-session.json', 'utf8'));
} catch (e) { process.exit(0); /* no session, nothing to report */ }

const endTime = new Date().toISOString();
const durationSeconds = Math.round(
  (new Date(endTime) - new Date(session.start_time)) / 1000
);

// Read state file for stage transitions
let stages = [];
try {
  const stateLines = fs.readFileSync('.claude/workflow-state.jsonl', 'utf8')
    .split('\n').filter(Boolean);
  stages = stateLines.map(line => JSON.parse(line));
} catch (e) { /* no state entries */ }

const stagesEntered = [...new Set(stages.filter(s => s.action === 'entered').map(s => s.stage))];
const stagesCompleted = [...new Set(stages.filter(s => s.action === 'completed').map(s => s.stage))];

// Detect entry point from first stage entered
const entryPoint = stagesEntered[0] || 'unknown';

// Check for spec file
let specCreated = false, specRequirementsCount = 0;
try {
  const specFiles = fs.readdirSync('docs/specs').filter(f => f.endsWith('.md'));
  // TODO: compare against git status to find newly created specs this session
  specCreated = specFiles.length > 0;
  if (specCreated) {
    const specContent = fs.readFileSync(`docs/specs/${specFiles[specFiles.length - 1]}`, 'utf8');
    specRequirementsCount = (specContent.match(/^- \[ \]/gm) || []).length;
  }
} catch (e) { /* no specs dir */ }

// Check git activity
let commitsCount = 0, filesChangedCount = 0;
try {
  const log = execSync(`git log --since="${session.start_time}" --oneline`, { encoding: 'utf8' });
  commitsCount = log.split('\n').filter(Boolean).length;
  if (commitsCount > 0) {
    const diff = execSync(`git diff --stat HEAD~${commitsCount} HEAD`, { encoding: 'utf8' });
    filesChangedCount = diff.split('\n').filter(l => l.includes('|')).length;
  }
} catch (e) { /* git errors */ }

// Determine outcome
let outcome = 'abandoned';
if (stagesCompleted.includes('finish')) outcome = 'branch_finished';
else if (stagesEntered.length > 0) outcome = 'in_progress';

const { sendEvent } = require('./kafka-producer');

async function main() {
  await sendEvent(
    { eventType: 'workflow.session.completed', sessionId: session.session_id,
      project: session.project, pluginVersion: session.plugin_version || 'unknown' },
    { total_duration_seconds: durationSeconds, entry_point: entryPoint,
      stages_entered: stagesEntered, stages_completed: stagesCompleted,
      spec_created: specCreated, spec_requirements_count: specRequirementsCount,
      commits_count: commitsCount, files_changed_count: filesChangedCount, outcome }
  );
  console.log(`[metrics] Session ${session.session_id} completed (${outcome}, ${durationSeconds}s)`);
}

main().catch(err => console.error('[metrics] Unexpected error:', err.message));
```

### Skill Integration: State File Writes

Each skill writes stage transitions to `.claude/workflow-state.jsonl`. This is a **minimal instruction** — one echo/append command per transition.

**Example (in spec-driven-development skill):**

At the start:
```
Append to .claude/workflow-state.jsonl: {"stage":"spec","action":"entered","timestamp":"<ISO8601>"}
```

When approved:
```
Append to .claude/workflow-state.jsonl: {"stage":"spec","action":"completed","timestamp":"<ISO8601>"}
```

**Same pattern for:** `plan`, `implement`, `review`, `finish`.

Even if the agent occasionally skips this instruction, the SessionStop hook still fires and emits whatever data is available, ensuring minimum viable metrics.

---

## Metrics Schema

### Event: `workflow.session.started`

**Emitted by:** SessionStart hook via Kafka

```json
{
  "event_type": "workflow.session.started",
  "timestamp": "2026-02-11T10:30:00Z",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "project": "checkout-service",
  "plugin_version": "1.2.0"
}
```

### Event: `workflow.session.completed`

**Emitted by:** SessionStop hook via Kafka (`workflow.session.completed` key = `session_id`)

```json
{
  "event_type": "workflow.session.completed",
  "timestamp": "2026-02-11T12:45:00Z",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "project": "checkout-service",
  "plugin_version": "1.2.0",
  "metadata": {
    "total_duration_seconds": 8100,
    "entry_point": "spec",
    "stages_entered": ["spec", "plan", "implement", "review"],
    "stages_completed": ["spec", "plan", "implement"],
    "spec_created": true,
    "spec_requirements_count": 8,
    "commits_count": 12,
    "files_changed_count": 7,
    "outcome": "in_progress"
  }
}
```

**Field Definitions:**

- `plugin_version`: Version of the fulcrum plugin (e.g., "1.2.0") - used to correlate config changes with workflow outcomes
- `entry_point`: First workflow stage entered (`spec`, `plan`, `unknown`)
- `stages_entered`: All stages that were started
- `stages_completed`: All stages that were explicitly completed
- `outcome`: `branch_finished` | `in_progress` | `abandoned`
- `spec_created`: Whether a spec document was created this session
- `spec_requirements_count`: Number of requirements in the spec (checkboxes)

---

## Commands

### `/spec [description]`

Invokes the `spec-driven-development` skill. Adapts based on input clarity.

- If a description is provided: evaluates whether it's well-defined or vague, proceeds accordingly
- If no description: asks the engineer what they want to build

**Flow:**
```
/spec Add user notification preferences    (well-defined → skip dialogue)
/spec I want to improve error handling     (vague → dialogue first)
  ↓
[Phase 0: optional dialogue if vague]
  ↓
Codebase analysis → generate task spec → present for review → iterate → approve
  ↓
Generate plan → present for review → approve
  ↓
Execute via Superpowers pipeline (worktree → implement → review → finish)
```

**Frontmatter Example:**

```yaml
---
name: spec
description: Create a structured task specification through codebase analysis and iterative refinement, then generate an implementation plan
---
```

### `/compound`

Invokes the compound learning skill.

- Gathers data from the most recent cycle
- Proposes learnings
- Applies approved updates to `docs/learnings/` and `CLAUDE.md`

**Flow:**
```
/compound
  ↓
Identify recent cycle → extract context → propose learnings → engineer reviews
  ↓
Apply approved learnings → update docs/learnings/ → update CLAUDE.md
```

**Frontmatter Example:**

```yaml
---
name: compound
description: Capture and apply learnings from completed development cycles
---
```

---

## Installation & Setup

### Prerequisites
- Claude Code CLI v2.1.0+
- Node.js 18+ (for hook scripts)

### Installation

```bash
# 1. Add the fulcrum marketplace
/plugin marketplace add {org}/fulcrum

# 2. Install the fulcrum plugin
/plugin install fulcrum@{org}/fulcrum

# 3. Quit and restart Claude Code

# 4. Verify installation
/help
# Should show: /spec, /compound alongside Superpowers commands
```

### First-Time Setup

No special per-project setup needed. The plugin works immediately:

1. Enterprise context is automatically loaded (approach TBD)
2. `.claude/project-config.md` is read if it exists in the repo
3. Project name is auto-detected from git remote URL

If a project doesn't have `.claude/project-config.md`, only company defaults are used. Engineers can create project config at any time by adding `.claude/project-config.md` to their repo.

---

## Testing Strategy

Each new skill should be tested following Superpowers' TDD for skills methodology:

1. **Define pressure scenarios**: situations where the skill might fail or produce undesirable behavior
2. **Establish baseline**: observe agent behavior WITHOUT the skill
3. **Write the skill**: create the SKILL.md
4. **Verify improvement**: observe agent behavior WITH the skill
5. **Refactor**: close loopholes and edge cases

### Key Test Scenarios

**Spec-Driven Development:**
- Simple task (< 30 min estimated) → spec is concise, doesn't over-engineer
- Complex task (multi-day) → spec is thorough, breaks into clear requirements
- Engineer rejects spec sections → iterates without losing approved sections
- No existing tests in codebase → spec still includes testing requirements from company config
- Spec created but engineer never approves → workflow stops at spec phase, no plan generated

**Enterprise Context:**
- Company config unavailable → skill logs warning, uses project config only, workflow continues
- No `.claude/project-config.md` in repo → uses company config only
- Project config overrides company config → override is applied correctly
- Malformed project config → logs error, uses company config only
- Git remote URL not available → project name defaults to "unknown", metrics still collected

**Compound Learning:**
- No notable learnings in a cycle → says so, doesn't force empty entries
- Learning duplicates an existing rule in CLAUDE.md → detects and skips
- Engineer rejects all learnings → no changes applied, no nagging
- Multiple cycles without `/compound` run → still works when finally invoked
- Learning applies to CLAUDE.md but file doesn't exist yet → creates it

**Metrics Hooks:**
- SessionStop fires with no state file → emits event with empty stages
- Git commands fail (not a git repo) → event still emitted with placeholder values
- State file has entries but no "completed" actions → outcome is "in_progress"
- Multiple sessions in same day → each gets unique session ID

---

## Adoption Strategy

### Phase 1: Install & Configure (Week 1)
- Fork Superpowers v4.1.1
- Add enterprise-context skill with structured config loading
- Create company standards config files in `config/company-standards/`
- Deploy as plugin to pilot team (5-10 engineers)
- Engineers install plugin and verify company config is automatically available
- No per-project setup needed — project name auto-detected from git remote

### Phase 2: Spec Command (Week 2-3)
- Add spec-driven-development skill and `/spec` command
- Engineers use `/spec` for all feature work — exploratory or well-defined
- Collect initial feedback on spec quality and workflow fit

### Phase 3: Metrics Instrumentation (Week 3-4)
- Configure Kafka env vars (`FULCRUM_KAFKA_BROKERS`, `FULCRUM_KAFKA_TOPIC`) on engineer machines
- Start collecting workflow data
- Build initial dashboard showing:
  - Session counts by project
  - Entry point distribution (spec vs write-plan vs direct)
  - Average session duration
  - Completion rates (abandoned vs in_progress vs branch_finished)

### Phase 4: Compound Learning (Week 4-5)
- Add compound-learning skill and `/compound` command
- Educate engineers on when to capture learnings
- Start building project-specific knowledge in `docs/learnings/`
- Observe learnings improving `CLAUDE.md` and skills over time

### Phase 5: Broader Rollout (Week 6-8)
- Roll out to additional teams based on pilot success
- Use metrics data to prove ROI and identify improvement areas
- Interview non-adopters to understand friction points
- Iterate on skills based on real usage patterns

---

## Open Questions & Future Considerations

### V1 Open Questions

1. **Config update frequency** — How often should company standards change? Recommend quarterly major updates, monthly minor updates

2. **Offline operation handling** — Current approach: workflow continues without config if files missing. Should we add better degradation messaging?

### Future Enhancements (v2+)

3. **Jira integration** — Once core workflow proves value, add back Jira integration for task context

4. **Automatic PR creation** — Hook into Bitbucket API to create PR after branch finish

5. **Multi-ticket workflows** — Support PRs that address multiple related tasks

6. **Metrics privacy** — Default to anonymized engineer IDs? Project-level aggregates as default view?

7. **Superpowers upstream sync** — How often to merge upstream changes? Need a process (monthly? quarterly?)

8. **Cross-project learning sharing** — Promote common learnings from projects into company config

9. **Config contribution process** — How do teams propose changes to company standards? Need PR review guidelines

---

## Success Criteria

The fulcrum succeeds if:

1. **Adoption** — Engineers choose to use it (not mandated) and continue using it
2. **Workflow efficiency** — Measurable time savings or quality improvements from metrics
3. **Metrics prove value** — Clear ROI demonstrated to leadership
4. **Team learning** — Knowledge accumulates in projects and improves outcomes
5. **Minimal friction** — Setup is quick (< 5 minutes), usage feels natural
6. **Scalability** — Works for 5-50+ engineers without per-team customization
