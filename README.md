# Fulcrum

A Claude Code plugin for enterprise software delivery teams. Combines [Superpowers](https://github.com/obra/superpowers) core skills with enterprise extensions for structured workflows, company standards, metrics, and continuous learning.

## What's included

### Core skills (from Superpowers)
- **`/write-plan`** — Detailed implementation planning with bite-sized tasks (use when requirements are already clear)
- **`/execute-plan`** — Multi-session plan execution with review checkpoints
- TDD, systematic debugging, code review, git worktrees, verification, branch finishing

### Enterprise extensions (new)
- **`/spec`** — Adaptive entry point for all feature work: dialogue for vague ideas, straight to analysis for well-defined tasks. Always produces a spec artifact → plan → execute
- **Enterprise context** — Automatically injects company coding standards, architecture patterns, and security requirements at the right phase (spec/plan/implement/review)
- **`/compound`** — Capture learnings from completed cycles into `docs/learnings/` and `CLAUDE.md`
- **Metrics hooks** — Collect session-level workflow data (duration, stages, commits, outcome)

## Installation

```bash
/plugin install fulcrum
/quit   # restart Claude Code
/help   # confirm /spec and /compound appear
```

Requires: Claude Code CLI v2.1.0+, Node.js 18+ (for metrics hooks)

## Usage

### Spec-driven development

Use `/spec` for any feature work — it adapts. For vague ideas it starts with dialogue; for well-defined tasks it goes straight to codebase analysis.

```
/spec Add email verification to user registration
/spec I want to improve how we handle errors
```

1. (If vague) Asks questions one at a time to clarify intent and explore approaches
2. Analyzes affected files and existing patterns
3. Loads company standards (architecture, coding, security)
4. Generates a structured spec → you review and iterate → approve
5. Generates an implementation plan → you approve
6. Executes via standard workflow: git worktree → TDD → code review → verify → finish

Specs are saved to `docs/specs/YYYY-MM-DD-description.md` as permanent artifacts.

### Compound learning

After finishing a feature or branch:

```
/compound
```

1. Identifies the recent development cycle (git history, spec, files changed)
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

The session-start hook writes `.claude/workflow-session.json` (session ID, project, plugin version). The stop hook emits a `workflow.session.completed` event to console (v1) with fields: duration, stages, commits, outcome.

To enable HTTP posting to your metrics backend, set `FULCRUM_METRICS_URL` and uncomment the `fetch()` calls in `hooks/metrics-session-end.js`.

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
  metrics-session-start.js
  metrics-session-end.js
config/company-standards/
  architecture.yaml
  coding-standards.yaml
  security.yaml
  testing.yaml
  git-workflow.yaml
```

## License

MIT — same as [Superpowers](https://github.com/obra/superpowers)
