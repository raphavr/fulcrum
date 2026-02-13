#!/usr/bin/env node

/**
 * Metrics Session Start Hook
 *
 * Initializes session tracking:
 * - Generates a unique session ID
 * - Detects project name from git remote
 * - Reads plugin version from plugin.json
 * - Writes session state to .claude/workflow-session.json
 * - Initializes empty workflow state file for stage transitions
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execSync } = require('child_process');
const { sendEvent } = require('./kafka-producer');

const sessionId = crypto.randomUUID();
const startTime = new Date().toISOString();

// Detect project name from git remote
let project = 'unknown';
try {
  const remoteUrl = execSync('git remote get-url origin', { encoding: 'utf8' }).trim();
  // Extract repo name from URL patterns:
  // git@bitbucket.org:company/checkout-service.git → checkout-service
  // https://bitbucket.org/company/checkout-service.git → checkout-service
  const match = remoteUrl.match(/\/([^/]+?)(?:\.git)?$/);
  if (match) project = match[1];
} catch (e) {
  // Not a git repo or no remote configured
}

// Get plugin version from plugin.json
let pluginVersion = 'unknown';
try {
  const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, '..');
  const pluginMeta = JSON.parse(
    fs.readFileSync(path.join(pluginRoot, '.claude-plugin', 'plugin.json'), 'utf8')
  );
  pluginVersion = pluginMeta.version || 'unknown';
} catch (e) {
  // plugin.json not found or malformed
}

// Initialize state directory and files
const stateDir = '.claude';
if (!fs.existsSync(stateDir)) {
  fs.mkdirSync(stateDir, { recursive: true });
}

fs.writeFileSync(
  path.join(stateDir, 'workflow-session.json'),
  JSON.stringify({
    session_id: sessionId,
    start_time: startTime,
    project,
    plugin_version: pluginVersion
  }, null, 2)
);

// Initialize empty state file for stage transitions
fs.writeFileSync(path.join(stateDir, 'workflow-state.jsonl'), '');

sendEvent(
  { eventType: 'workflow.session.started', sessionId, project, pluginVersion },
  {}
).then(() => {
  console.log(`[metrics] Session ${sessionId} started for project ${project} (plugin v${pluginVersion})`);
}).catch((err) => {
  console.error('[metrics] Unexpected error:', err.message);
});
