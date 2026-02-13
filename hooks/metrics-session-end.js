#!/usr/bin/env node

/**
 * Metrics Session End Hook
 *
 * Reads artifacts (state file, git history, specs) and emits
 * a workflow.session.completed event with session metrics.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { sendEvent } = require('./kafka-producer');

async function main() {
  // Read session info
  let session = {};
  try {
    session = JSON.parse(
      fs.readFileSync('.claude/workflow-session.json', 'utf8')
    );
  } catch (e) {
    // No session file — nothing to report
    return;
  }

  const endTime = new Date().toISOString();
  const durationSeconds = Math.round(
    (new Date(endTime) - new Date(session.start_time)) / 1000
  );

  // Read state file for stage transitions
  let stages = [];
  try {
    const stateLines = fs
      .readFileSync('.claude/workflow-state.jsonl', 'utf8')
      .split('\n')
      .filter(Boolean);
    stages = stateLines.map((line) => JSON.parse(line));
  } catch (e) {
    // No state entries
  }

  const stagesEntered = [
    ...new Set(stages.filter((s) => s.action === 'entered').map((s) => s.stage))
  ];
  const stagesCompleted = [
    ...new Set(stages.filter((s) => s.action === 'completed').map((s) => s.stage))
  ];

  // Detect entry point from first stage entered
  const entryPoint = stagesEntered[0] || 'unknown';

  // Check for spec file
  let specCreated = false;
  let specRequirementsCount = 0;
  try {
    const specsDir = 'docs/specs';
    if (fs.existsSync(specsDir)) {
      const specFiles = fs.readdirSync(specsDir).filter((f) => f.endsWith('.md'));
      specCreated = specFiles.length > 0;
      if (specCreated) {
        const latestSpec = specFiles[specFiles.length - 1];
        const specContent = fs.readFileSync(path.join(specsDir, latestSpec), 'utf8');
        specRequirementsCount = (specContent.match(/^- \[ \]/gm) || []).length;
      }
    }
  } catch (e) {
    // No specs dir
  }

  // Check git activity since session start
  let commitsCount = 0;
  let filesChangedCount = 0;
  try {
    const log = execSync(
      `git log --since="${session.start_time}" --oneline`,
      { encoding: 'utf8' }
    );
    commitsCount = log.split('\n').filter(Boolean).length;
    if (commitsCount > 0) {
      const diff = execSync(
        `git diff --stat HEAD~${commitsCount} HEAD`,
        { encoding: 'utf8' }
      );
      filesChangedCount = diff.split('\n').filter((l) => l.includes('|')).length;
    }
  } catch (e) {
    // Git errors (not a repo, no commits, etc.)
  }

  // Determine outcome
  let outcome = 'abandoned';
  if (stagesCompleted.includes('finish')) {
    outcome = 'branch_finished';
  } else if (stagesEntered.length > 0) {
    outcome = 'in_progress';
  }

  await sendEvent(
    {
      eventType:     'workflow.session.completed',
      sessionId:     session.session_id,
      project:       session.project,
      pluginVersion: session.plugin_version || 'unknown',
    },
    {
      total_duration_seconds:  durationSeconds,
      entry_point:             entryPoint,
      stages_entered:          stagesEntered,
      stages_completed:        stagesCompleted,
      spec_created:            specCreated,
      spec_requirements_count: specRequirementsCount,
      commits_count:           commitsCount,
      files_changed_count:     filesChangedCount,
      outcome,
    }
  );

  console.log(`[metrics] Session ${session.session_id} completed (${outcome}, ${durationSeconds}s)`);
}

main().catch((err) => console.error('[metrics] Unexpected error:', err.message));
