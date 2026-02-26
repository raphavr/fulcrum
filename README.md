# Fulcrum

A Claude Code plugin for enterprise software delivery teams. Combines [Superpowers](https://github.com/obra/superpowers) core skills with enterprise extensions for structured workflows, company standards, metrics, and continuous learning.

## The delivery pipeline

Every feature follows the same four-stage flow:

```
/spec  →  /write-plan  →  /execute-plan  →  /compound
  │              │                │               │
Spec         Plan doc         Working         Learnings
artifact     saved to         branch          saved to
saved to     docs/plans/      merged or       docs/learnings/
docs/specs/                   PR open         + CLAUDE.md
```

Each command hands off to the next. You do not run them in isolation.

## Installation

Fulcrum is not listed in the Anthropic marketplace. Install it by pointing Claude Code at this repo as a custom marketplace:

```bash
/plugin marketplace add https://github.com/raphavr/fulcrum
/plugin install fulcrum
/quit   # restart Claude Code
/help   # confirm /spec and /compound appear
```

Requires: Claude Code CLI v2.1.0+, Python 3.8+ (for metrics hooks)

## Usage

### Stage 1 — `/spec`

Start every feature here. Adapts to how clear the idea is.

```
/spec Add email verification to user registration
/spec I want to improve how we handle errors
```

1. (If vague) Asks focused questions to clarify intent and explore approaches
2. Analyzes affected files and existing patterns in the codebase
3. Loads company standards (architecture, coding, security)
4. Generates a structured spec at `docs/specs/YYYY-MM-DD-description.md` → you review and approve

**Hands off to `/write-plan` automatically once the spec is approved.**

---

### Stage 2 — `/write-plan`

Turns the approved spec into a bite-sized implementation plan.

- Reads the spec doc and project `CLAUDE.md` for test patterns and commit conventions
- Produces a plan at `docs/plans/YYYY-MM-DD-feature.md` with exact file paths, full code, and TDD steps
- Each task is 2–5 minutes: write failing test → implement → verify → commit

**Hands off to `/execute-plan` (separate session) or runs subagent-driven execution in the current session.**

---

### Stage 3 — `/execute-plan`

Executes the plan task by task with review checkpoints.

- Verifies you are in a feature branch worktree (creates one if not)
- Runs tasks in batches of 3, reports after each batch
- After all tasks: verifies tests, then presents merge/PR/keep/discard options

**Hands off to `/compound` after the branch is finished.**

---

### Stage 4 — `/compound`

Captures what was learned from the completed cycle.

```
/compound
```

1. Identifies the cycle from git history, spec, and changed files
2. Proposes learnings by category: patterns, gotchas, tools, process, false starts
3. You approve each learning
4. Saves to `docs/learnings/` and updates `CLAUDE.md`

### Company standards

Standards are loaded automatically from `config/company-standards/`:

| File | Contents | Loaded during |
|------|----------|---------------|
| `architecture.yaml` | Backend/API patterns | Spec |
| `coding-standards.yaml` | Style, naming, line length | Spec, Implement |
| `security.yaml` | Secrets, queries, auth | Spec |
| `testing.yaml` | Coverage, test types | Plan |
| `git-workflow.yaml` | Branch, commit, merge | Plan |

Projects can override any setting by creating `.claude/project-config.md`:

```yaml
# Example: checkout-service overrides
architecture:
  communication_pattern: "sync-http"
testing:
  min_coverage: 95
```

### Metrics

The session-start hook writes `.claude/workflow-session.json` (session ID, project, plugin version). The stop hook emits a `workflow.session.completed` event with fields: duration, stages, commits, outcome.

Events are sent to Kafka. Set these environment variables to enable:

| Variable | Description |
|---|---|
| `FULCRUM_KAFKA_BROKERS` | Comma-separated broker list (required) |
| `FULCRUM_KAFKA_TOPIC` | Topic name for all events (required) |
| `FULCRUM_KAFKA_CLIENT_ID` | Producer client ID (default: `fulcrum-plugin`) |
| `FULCRUM_KAFKA_SSL` | Enable TLS — `true` or `false` (default: `false`) |
| `FULCRUM_KAFKA_SASL_USERNAME` | SASL plain username (optional) |
| `FULCRUM_KAFKA_SASL_PASSWORD` | SASL plain password (optional) |

When the Kafka variables are not set the hooks run silently and skip emission. Install the Kafka client with `pip install confluent-kafka` (or `pip install -r hooks/requirements.txt`).

## Customise company standards

Edit the YAML files in `config/company-standards/` to match your organisation. Distribute changes by bumping the plugin version — engineers run `/plugin update fulcrum` and pick up the new standards on next session.

## Project structure

```
.claude-plugin/          plugin.json, marketplace.json
skills/
  writing-plans/         core Superpowers skills
  subagent-driven-development/
  test-driven-development/
  systematic-debugging/
  … (12 more)
  spec-driven-development/   Fulcrum enterprise skills
  enterprise-context/
  compound-learning/
commands/
  spec.md                /spec — adaptive entry point (exploratory or well-defined)
  write-plan.md          /write-plan — mid-pipeline entry (requirements already clear)
  execute-plan.md        /execute-plan
  compound.md            /compound
hooks/
  session-start.sh       bootstraps skills context (Superpowers)
  hooks.json             SessionStart + Stop
  kafka_producer.py
  metrics_session_start.py
  metrics_session_end.py
  requirements.txt
config/company-standards/
  architecture.yaml
  coding-standards.yaml
  security.yaml
  testing.yaml
  git-workflow.yaml
```

## License

MIT — same as [Superpowers](https://github.com/obra/superpowers)
